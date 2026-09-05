"""数据抓取与 Cookie 管理：模拟小程序请求，登录失效抛 AuthError。"""
import json
import os
from datetime import datetime, timedelta

import requests

from config import (
    AUTH_FAIL_CODE, BULK_CRAWL_THRESHOLD, CRAWLER_BASE_URL, CRAWLER_ENDPOINTS,
    CRAWLER_HEADERS, CRAWLER_SESSION_FILE, DATA_RETENTION_DAYS,
    SESSION_COOKIE_NAME,
)
from models import Comment, Message, Post, SessionLocal, UserAction


class AuthError(Exception):
    """登录失效，需更新 Cookie。"""


def load_session():
    """从 session.json 读取 Session（兼容文档别名 ys7_ysxy_session）。"""
    if not os.path.exists(CRAWLER_SESSION_FILE):
        return None
    with open(CRAWLER_SESSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(SESSION_COOKIE_NAME) or data.get("ys7_ysxy_session")


def save_session(value):
    with open(CRAWLER_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump({SESSION_COOKIE_NAME: value}, f, ensure_ascii=False)


def _headers():
    h = dict(CRAWLER_HEADERS)
    sess = load_session()
    if sess:
        h["Cookie"] = f"{SESSION_COOKIE_NAME}={sess}"
    return h


def _post(path, payload):
    r = requests.post(CRAWLER_BASE_URL + path, json=payload,
                      headers=_headers(), timeout=10)
    try:
        data = r.json()
    except ValueError:
        raise AuthError(f"非 JSON 响应: {r.status_code}")
    if data.get("code") == AUTH_FAIL_CODE:
        raise AuthError(data.get("message", "请先登录"))
    return data


def fetch_list(kind="latest", page=1, limit=20):
    """抓取列表（latest / reply / hot），返回帖子 dict 列表。"""
    data = _post(CRAWLER_ENDPOINTS[kind], {"page": page, "limit": limit})
    return data.get("data", {}).get("list", []) or []


def fetch_detail(article_id):
    """抓取帖子详情。"""
    data = _post(CRAWLER_ENDPOINTS["detail"], {"id": article_id})
    return data.get("data", {})


def save_posts(raw_posts):
    """清洗 + 分区/类型归类 + 入库（按源 id 去重），返回新入库的 (source_id, db_id) 列表。"""
    from utils.recommender import classify, detect_post_type

    db = SessionLocal()
    saved = []
    for p in raw_posts:
        sid = p.get("id")
        if not sid:
            continue
        if db.query(Post).filter(Post.source_id == sid).first():
            continue
        detail = p.get("detail") or ""
        if not detail:
            continue
        title = (p.get("title") or "").strip() or detail[:30]
        source_name = p.get("category_name") or ""
        zone = classify(detail, source_name=source_name)
        ptype = detect_post_type(title, detail, source_name=source_name)
        post = Post(
            source_id=sid, title=title, content=detail, category=zone,
            zone=zone, source_category_id=p.get("category_id"),
            source_category_name=source_name,
            hot=p.get("hot") or 0, post_type=ptype, source_url=CRAWLER_BASE_URL,
            created_at=_parse_time(p.get("create_time")),
        )
        db.add(post)
        db.flush()  # 取得 post.id 供评论关联
        saved.append((sid, post.id))
    db.commit()
    db.close()
    return saved


def _parse_time(s):
    if not s:
        return datetime.now()
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return datetime.now()


def save_comments(source_post_id, raw_comment_list):
    """解析 comment_list，写入 Comment（question/answer 楼中楼），返回结构化数组。

    detail → answer；reply_comment_id → question（0 → 无（初始帖子评论），否则回溯父评论 detail）。
    """
    by_source = {c.get("id"): c for c in raw_comment_list if c.get("id") is not None}
    structured = []
    db = SessionLocal()
    try:
        for c in raw_comment_list:
            cid = c.get("id")
            answer = (c.get("detail") or "").strip()
            if not answer:
                continue
            reply_id = c.get("reply_comment_id") or 0
            if reply_id and reply_id in by_source:
                question = (by_source[reply_id].get("detail") or "").strip()
            else:
                question = "无（初始帖子评论）"
            structured.append({"question": question, "answer": answer})

            # 入库（按源评论 id 去重）
            exists = db.query(Comment).filter(Comment.source_id == cid).first()
            if exists:
                continue
            db.add(Comment(
                post_id=source_post_id, user_id=0, content=answer,
                reply_comment_id=int(reply_id) if reply_id else 0, source_id=cid,
                created_at=_parse_time(c.get("create_time")),
            ))
        db.commit()
    finally:
        db.close()
    return structured


def crawl_comments_for_new(pairs, limit_per_post=50):
    """对新增帖子抓取评论，返回 {source_id: [{question, answer}]}。"""
    result = {}
    for sid, db_id in pairs:
        try:
            detail = fetch_detail(sid)
            raw = detail.get("comment_list") or []
            structured = save_comments(db_id, raw[:limit_per_post])
            result[sid] = structured
        except AuthError:
            raise
        except Exception as e:
            print(f"[crawler] 评论抓取失败 sid={sid}: {e}", flush=True)
    return result


def _bulk_fetch():
    """分页全量抓取 latest，直到空页。"""
    all_posts = []
    page = 1
    while True:
        batch = fetch_list("latest", page=page, limit=50)
        if not batch:
            break
        all_posts.extend(batch)
        page += 1
        if page > 1000:  # 安全上限
            break
    return all_posts


def run():
    """全量（<阈值）或增量抓取，入库 + 评论 + 触发推荐矩阵更新。"""
    try:
        db = SessionLocal()
        try:
            count = db.query(Post).count()
        finally:
            db.close()

        if count < BULK_CRAWL_THRESHOLD:
            raw = _bulk_fetch()
            mode = "全量"
        else:
            raw = fetch_list("latest", page=1, limit=20)
            mode = "增量"

        pairs = save_posts(raw)
        comments = crawl_comments_for_new(pairs)
        n_comments = sum(len(v) for v in comments.values())
        print(f"[crawler] {mode}抓取完成，新增 {len(pairs)} 条、评论 {n_comments} 条", flush=True)

        from utils.recommender import update_matrix
        update_matrix()
        return pairs
    except AuthError as e:
        print(f"[crawler] 登录失效: {e} —— 请运行 mitm_proxy 或手动更新 session.json", flush=True)
        return []


def cleanup_old(days=DATA_RETENTION_DAYS):
    """删除超过 N 天的过期数据。"""
    cutoff = datetime.now() - timedelta(days=days)
    db = SessionLocal()
    for model, col in ((Post, Post.created_at),
                       (UserAction, UserAction.timestamp),
                       (Message, Message.created_at),
                       (Comment, Comment.created_at)):
        n = db.query(model).filter(col < cutoff).delete()
        print(f"[cleanup] 删除 {model.__name__} {n} 条过期记录")
    db.commit()
    db.close()
