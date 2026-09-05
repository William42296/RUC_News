"""首页：推荐流、最新、悬赏、大事件、分区。"""
import json
from collections import Counter

import jieba
from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from config import (KEY_LIST_LATEST, RECOMMEND_TOP_N, ZONE_NAMES, ok,
                    redis_client)
from models import Post, SessionLocal
from utils.recommender import recommend

main_bp = Blueprint("main", __name__)


def _serialize(p):
    return {
        "id": p.id, "title": p.title, "content": p.content[:100],
        "category": p.category, "zone": p.zone,
        "category_name": p.source_category_name,
        "post_type": p.post_type, "hot": p.hot,
        "status": p.status, "reward": p.reward,
        "team_cur": p.team_cur, "team_total": p.team_total,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _list_resp(posts, total, page, limit):
    last = posts[0].created_at if posts else None
    return ok({
        "posts": [_serialize(p) for p in posts],
        "total": total,
        "page": page,
        "has_more": page * limit < total,
        "last_post_time": last.isoformat() if last else None,
    })


def _latest_from_db(page, limit, zone=None):
    db = SessionLocal()
    try:
        q = db.query(Post)
        if zone is not None:
            q = q.filter(Post.zone == int(zone))
        total = q.count()
        posts = (q.order_by(Post.created_at.desc())
                 .offset((page - 1) * limit).limit(limit).all())
        return posts, total
    finally:
        db.close()


@main_bp.route("/")
def home():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", RECOMMEND_TOP_N))
    user_id = getattr(g, "user_id", None)
    if user_id is None:
        posts, total = _latest_from_db(page, limit)
        return jsonify(_list_resp(posts, total, page, limit))
    posts, total = recommend(user_id, top_n=limit, page=page, limit=limit)
    return jsonify(_list_resp(posts, total, page, limit))


@main_bp.route("/latest")
def latest():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    zone = request.args.get("zone")  # 分区过滤（可选，1-36）
    if zone is not None:
        zone = int(zone)
    if page == 1 and zone is None:
        cached = redis_client.get(KEY_LIST_LATEST)
        if cached:
            return jsonify(json.loads(cached))
    posts, total = _latest_from_db(page, limit, zone=zone)
    resp = _list_resp(posts, total, page, limit)
    if page == 1 and zone is None:
        redis_client.set(KEY_LIST_LATEST, json.dumps(resp), ex=60)
    return jsonify(resp)


@main_bp.route("/bounty")
def bounty():
    btype = request.args.get("type", "lost")
    status = request.args.get("status", "unfinished")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    post_type = "team" if btype == "team" else ("secondhand" if btype == "secondhand" else "lost")
    db = SessionLocal()
    try:
        q = db.query(Post).filter(Post.post_type == post_type)
        if status in ("unfinished", "finished"):
            q = q.filter(Post.status == status)
        total = q.count()
        posts = (q.order_by(Post.created_at.desc())
                 .offset((page - 1) * limit).limit(limit).all())
        return jsonify(_list_resp(posts, total, page, limit))
    finally:
        db.close()


# ---------- 大事件：同一事件分组 ----------

_STOPWORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没",
    "看", "好", "自己", "这", "那", "与", "及", "或", "等", "该", "被", "把",
    "啊", "吧", "吗", "呢", "哦", "对", "从", "请", "还", "已", "给", "让",
    "今天", "昨天", "明天", "现在", "一下", "大家", "同学", "我们", "你们", "他们",
}


def _keywords(blob):
    return [w for w in jieba.lcut(blob or "")
            if len(w.strip()) >= 2 and not w.isdigit() and w not in _STOPWORDS]


def _group_events(posts):
    """两两共享 ≥2 关键词判同组，连通分量合并，组内按时间排序。"""
    kws = {p.id: set(_keywords(f"{p.title} {p.content}")) for p in posts}
    parent = {p.id: p.id for p in posts}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    ids = list(kws.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if len(kws[ids[i]] & kws[ids[j]]) >= 2:
                union(ids[i], ids[j])

    groups = {}
    for p in posts:
        groups.setdefault(find(p.id), []).append(p)
    return groups


def _build_events():
    db = SessionLocal()
    try:
        candidates = (db.query(Post).filter(Post.post_type == "event")
                      .order_by(Post.created_at.desc()).limit(200).all())
        if len(candidates) < 5:
            extra = (db.query(Post).order_by(Post.hot.desc(), Post.created_at.desc())
                     .limit(200).all())
            seen = {p.id for p in candidates}
            candidates.extend([p for p in extra if p.id not in seen][:200 - len(candidates)])

        groups = _group_events(candidates)
        result = []
        for gid, members in groups.items():
            members.sort(key=lambda p: p.created_at)
            # 事件标题：最高频关键词，兜底用最早节点标题
            all_kws = Counter()
            for p in members:
                all_kws.update(set(_keywords(f"{p.title} {p.content}")))
            title = all_kws.most_common(1)[0][0] if all_kws else members[0].title
            result.append({
                "event_id": members[0].id,
                "title": title,
                "nodes": [
                    {"id": p.id, "title": p.title, "detail": p.content,
                     "date": p.created_at.strftime("%Y-%m-%d") if p.created_at else ""}
                    for p in members
                ],
            })
        result.sort(key=lambda e: e["nodes"][-1]["date"], reverse=True)
        return result
    finally:
        db.close()


@main_bp.route("/events")
def events():
    return jsonify(ok({"events": _build_events()}))


@main_bp.route("/events/<int:eid>")
def event_detail(eid):
    for ev in _build_events():
        if ev["event_id"] == eid:
            return jsonify(ok({"event": ev}))
    return jsonify(ok({"event": None}))


@main_bp.route("/zones")
def zones():
    db = SessionLocal()
    try:
        rows = (db.query(Post.zone, func.count(Post.id)).group_by(Post.zone).all())
        counts = {z: n for z, n in rows}
        cats = [{"id": z, "name": ZONE_NAMES[z], "count": counts.get(z, 0)}
                for z in sorted(ZONE_NAMES)]
        return jsonify(ok({"zones": cats}))
    finally:
        db.close()


@main_bp.route("/categories")
def categories():
    """兼容旧分区接口，返回 36 内容分区。"""
    return zones()
