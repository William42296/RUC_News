"""搜索服务：全文检索（SQLite LIKE，ORM 参数化防注入）+ 热门搜索。"""
import json
import time

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from config import HOT_SEARCH_N, KEY_SEARCH, SEARCH_TTL, ok, redis_client
from models import Post, SessionLocal, UserAction

search_bp = Blueprint("search", __name__, url_prefix="/search")


@search_bp.route("")
def search():
    keyword = (request.args.get("keyword") or "").strip()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    post_type = (request.args.get("post_type") or "").strip()  # 快捷分类过滤
    valid_types = ("secondhand", "lost", "team")
    if not keyword and post_type not in valid_types:
        return jsonify(ok({"posts": [], "total": 0, "page": page,
                           "has_more": False, "search_time_ms": 0}))

    cache_key = KEY_SEARCH.format(f"{keyword}:{post_type}", page)
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))

    t0 = time.time()
    db = SessionLocal()
    try:
        q = db.query(Post)
        if keyword:
            like = f"%{keyword}%"
            q = q.filter(Post.title.like(like) | Post.content.like(like))
        if post_type in valid_types:
            q = q.filter(Post.post_type == post_type)
        total = q.count()
        posts = (q.order_by(Post.created_at.desc())
                 .offset((page - 1) * limit).limit(limit).all())
        resp = ok({
            "posts": [{"id": p.id, "title": p.title, "content": p.content[:100],
                       "category": p.category, "zone": p.zone,
                       "post_type": p.post_type,
                       "created_at": p.created_at.isoformat() if p.created_at else None}
                      for p in posts],
            "total": total,
            "page": page,
            "has_more": page * limit < total,
            "search_time_ms": round((time.time() - t0) * 1000, 2),
        })
    finally:
        db.close()
    redis_client.set(cache_key, json.dumps(resp), ex=SEARCH_TTL)
    return jsonify(resp)


@search_bp.route("/hot")
def hot():
    """大家都在搜：点击量最高的帖子标题。"""
    offset = int(request.args.get("offset", 0))
    db = SessionLocal()
    try:
        # 行为点击聚合 + 热度兜底
        rows = (db.query(Post.id, Post.title, func.count(UserAction.id).label("clicks"))
                .join(UserAction, UserAction.post_id == Post.id)
                .group_by(Post.id, Post.title)
                .order_by(func.count(UserAction.id).desc())
                .offset(offset).limit(HOT_SEARCH_N).all())
        if not rows:
            rows = (db.query(Post.id, Post.title, Post.hot)
                    .order_by(Post.hot.desc())
                    .offset(offset).limit(HOT_SEARCH_N).all())
            hot_list = [{"id": r.id, "title": r.title, "clicks": r.hot} for r in rows]
        else:
            hot_list = [{"id": r.id, "title": r.title, "clicks": r.clicks} for r in rows]
        return jsonify(ok({"hot": hot_list}))
    finally:
        db.close()
