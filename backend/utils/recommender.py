"""推荐算法：jieba 分区归类 + 用户-分区协同过滤 + 多目标打分 + E-E 探索利用。"""
import json

import jieba
import numpy as np
import pandas as pd
from sqlalchemy import func

from config import (
    EXPLORE_RATIO, KEY_MATRIX, MATRIX_TTL, POST_TYPE_KEYWORDS,
    RECOMMEND_TOP_N, W_CTR, W_ENGAGE, W_INTEREST, ZONE_DEFAULT, ZONE_KEYWORDS,
    ZONE_NAMES, redis_client,
)
from models import Comment, Like, Post, SessionLocal, UserAction


def classify(text, source_name=None):
    """返回内容分区 id (1-36)。source_name 仅作为分词上下文（不使用源站标签直接归类）。"""
    blob = f"{source_name or ''} {text or ''}".strip()
    if not blob:
        return ZONE_DEFAULT
    tokens = set(jieba.lcut(blob))
    scores = {}
    for z, kws in ZONE_KEYWORDS.items():
        # 子串匹配为主（特征词多为词组），分词结果兜底
        scores[z] = sum(1 for kw in kws if kw in blob) + sum(1 for kw in kws if kw in tokens)
    best = max(scores, key=scores.get)
    return best if scores[best] else ZONE_DEFAULT


def detect_post_type(title, content, source_name=None):
    """独立判定业务类型（与 zone 解耦），返回 lost/secondhand/team/event/normal。"""
    blob = f"{title or ''} {content or ''} {source_name or ''}"
    best_type, best_score = "normal", 0
    for ptype, kws in POST_TYPE_KEYWORDS.items():
        score = sum(1 for kw in kws if kw in blob)
        if score > best_score:
            best_type, best_score = ptype, score
    if source_name in EVENT_SOURCE_CATEGORIES:
        return "event"
    return best_type


# 源平台「公告/大事」类分区 → 大事件（post_type=event，供 /events 时间轴）
EVENT_SOURCE_CATEGORIES = {"反诈提醒", "放假", "新闻科研公示", "推免"}


def index_post(post_id, title, content, source_name=None):
    """发帖/入库后实时归类，写入 zone + post_type，返回 (zone, post_type)。"""
    blob = f"{title} {content}"
    zone = classify(blob, source_name=source_name)
    ptype = detect_post_type(title, content, source_name=source_name)
    db = SessionLocal()
    db.query(Post).filter(Post.id == post_id).update(
        {"zone": zone, "post_type": ptype})
    db.commit()
    db.close()
    return zone, ptype


def _cosine(m):
    """行向量余弦相似度矩阵。"""
    norm = np.linalg.norm(m, axis=1, keepdims=True)
    norm[norm == 0] = 1
    return (m / norm) @ (m / norm).T


def _user_zone_rates(db):
    """返回 {zone: {user_id: rate}}，行归一化后的用户-分区点击率。"""
    rows = (
        db.query(UserAction.user_id, Post.zone, func.count(UserAction.id))
        .join(Post, Post.id == UserAction.post_id)
        .group_by(UserAction.user_id, Post.zone)
        .all()
    )
    df = pd.DataFrame(rows, columns=["user_id", "zone", "clicks"])
    if df.empty:
        return {}
    mat = df.pivot_table(index="user_id", columns="zone",
                         values="clicks", fill_value=0.0)
    rates = mat.div(mat.sum(axis=1), axis=0).fillna(0.0)
    return {int(z): rates[z].to_dict() for z in rates.columns}


def update_matrix():
    """聚合 用户-分区点击率矩阵，算余弦相似度，回写 Redis。"""
    db = SessionLocal()
    try:
        rates = _user_zone_rates(db)
    finally:
        db.close()
    if not rates:
        return
    df = pd.DataFrame(rates).T.fillna(0.0)  # user_id -> {zone: rate}
    sim = _cosine(df.values)
    payload = json.dumps({"users": [int(u) for u in df.index], "matrix": sim.tolist()})
    redis_client.set(KEY_MATRIX, payload, ex=MATRIX_TTL)


def _zone_interest_scores(db, user_id):
    """协同过滤：返回 {zone: 预测兴趣分}（0~1，仅未点击分区）。"""
    cached = redis_client.get(KEY_MATRIX)
    if cached is None:
        update_matrix()
        cached = redis_client.get(KEY_MATRIX)
    if not cached:
        return {}
    payload = json.loads(cached)
    users = payload["users"]
    if user_id not in users:
        return {}
    sim = np.array(payload["matrix"])
    i = users.index(user_id)
    clicked = {
        z for (z,) in db.query(Post.zone)
        .join(UserAction, UserAction.post_id == Post.id)
        .filter(UserAction.user_id == user_id).distinct()
    }
    rates = _user_zone_rates(db)
    scores = {}
    for z in range(1, len(ZONE_NAMES) + 1):
        if z in clicked or z not in rates:
            continue
        col = rates[z]
        num = denom = 0.0
        for j, u in enumerate(users):
            if u == user_id or u not in col:
                continue
            w = sim[i][j]
            num += w * col[u]
            denom += abs(w)
        if denom:
            scores[z] = num / denom
    return scores


def _ctr(post):
    """预估点击率：点击+浏览数归一（+1 平滑）。"""
    return min((post.hot or 0) / 1000.0, 1.0)


def _engage_rate(db, post_id):
    """互动率：赞+评论 归一（+1 平滑）。"""
    n = (db.query(Like).filter(Like.post_id == post_id).count()
         + db.query(Comment).filter(Comment.post_id == post_id).count())
    return min(n / 50.0, 1.0)


def recommend(user_id, top_n=RECOMMEND_TOP_N, page=1, limit=None):
    """多目标加权打分，按得分降序返回；含 E-E 探索；支持分页（无限滚动）。"""
    limit = limit or top_n
    db = SessionLocal()
    try:
        total = db.query(Post).count()
        if total == 0:
            return [], 0

        interest = _zone_interest_scores(db, user_id)
        posts = db.query(Post).all()
        scored = []
        for p in posts:
            s_interest = interest.get(p.zone, 0.0)
            s_ctr = _ctr(p)
            s_eng = _engage_rate(db, p.id)
            score = W_INTEREST * s_interest + W_CTR * s_ctr + W_ENGAGE * s_eng
            scored.append((score, p))

        # 探索与利用（E-E）：长尾内容按比例混入排序，防止信息茧房
        scored.sort(key=lambda t: t[0], reverse=True)
        n_explore = max(1, int(len(scored) * EXPLORE_RATIO))
        exploit = scored[: max(0, len(scored) - n_explore)]
        explore_pool = scored[len(scored) - n_explore:] if scored else []

        # 每 step 条「利用」插入 1 条「探索」，保证每页都混入长尾
        step = max(1, len(exploit) // (len(explore_pool) + 1))
        ordered, e_idx = [], 0
        for i, (_, p) in enumerate(exploit):
            ordered.append(p)
            if e_idx < len(explore_pool) and (i + 1) % step == 0:
                ordered.append(explore_pool[e_idx][1])
                e_idx += 1
        while e_idx < len(explore_pool):
            ordered.append(explore_pool[e_idx][1])
            e_idx += 1

        start = (page - 1) * limit
        return ordered[start:start + limit], len(ordered)
    finally:
        db.close()


def _latest(db, top_n):
    return db.query(Post).order_by(Post.created_at.desc()).limit(top_n).all()
