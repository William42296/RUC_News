"""用户中心：登录（验证 Session 换 JWT）、行为上报。"""
import hashlib
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, g, jsonify, request

from config import JWT_ALGO, JWT_EXPIRE_HOURS, SECRET_KEY, err, ok
from models import (CoinTransaction, Comment, Like, Post, SessionLocal, User,
                    UserAction)
from utils import crawler, recommender

my_bp = Blueprint("my", __name__, url_prefix="/my")


def _serialize_post(p):
    return {
        "id": p.id, "title": p.title, "content": p.content[:100],
        "zone": p.zone, "post_type": p.post_type, "hot": p.hot,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@my_bp.route("/login", methods=["POST"])
def login():
    sess = crawler.load_session()
    if not sess:
        return jsonify(err(401, "无有效 Session")), 401
    try:
        crawler.fetch_list("latest", page=1, limit=1)  # 轻量验证
    except crawler.AuthError:
        return jsonify(err(401, "Session 已失效")), 401

    openid = hashlib.md5(sess.encode()).hexdigest()
    db = SessionLocal()
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        user = User(openid=openid, nickname=f"用户{openid[:6]}")
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()

    exp = datetime.now() + timedelta(hours=JWT_EXPIRE_HOURS)
    token = jwt.encode({"sub": str(user.id), "exp": exp}, SECRET_KEY, algorithm=JWT_ALGO)
    return jsonify(ok({"token": token, "user_id": user.id, "nickname": user.nickname}))


@my_bp.route("/feedback", methods=["POST"])
def feedback():
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    action_type = data.get("action_type", "click")
    if not post_id or action_type not in ("click", "view"):
        return jsonify(err(400, "post_id 或 action_type 非法")), 400

    db = SessionLocal()
    db.add(UserAction(user_id=g.user_id, post_id=post_id, action_type=action_type))
    db.commit()
    db.close()

    recommender.update_matrix()
    return jsonify(ok())


@my_bp.route("/posts")
def my_posts():
    """我发：我发布的帖子。"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    db = SessionLocal()
    try:
        q = db.query(Post).filter(Post.owner_id == g.user_id)
        total = q.count()
        posts = (q.order_by(Post.created_at.desc())
                 .offset((page - 1) * limit).limit(limit).all())
        return jsonify(ok({
            "posts": [_serialize_post(p) for p in posts],
            "total": total, "page": page,
            "has_more": page * limit < total,
        }))
    finally:
        db.close()


@my_bp.route("/replies")
def my_replies():
    """我回：我发布的评论（含所属帖子）。"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    db = SessionLocal()
    try:
        q = db.query(Comment).filter(Comment.user_id == g.user_id)
        total = q.count()
        rows = (q.order_by(Comment.created_at.desc())
                .offset((page - 1) * limit).limit(limit).all())
        items = []
        for c in rows:
            post = db.get(Post, c.post_id)
            items.append({
                "id": c.id, "content": c.content, "post_id": c.post_id,
                "post_title": post.title if post else "",
                "reply_comment_id": c.reply_comment_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })
        return jsonify(ok({
            "replies": items, "total": total, "page": page,
            "has_more": page * limit < total,
        }))
    finally:
        db.close()


@my_bp.route("/likes")
def my_likes():
    """我赞：我点赞过的帖子。"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    db = SessionLocal()
    try:
        q = (db.query(Post).join(Like, Like.post_id == Post.id)
             .filter(Like.user_id == g.user_id))
        total = q.count()
        posts = (q.order_by(Like.created_at.desc())
                 .offset((page - 1) * limit).limit(limit).all())
        return jsonify(ok({
            "posts": [_serialize_post(p) for p in posts],
            "total": total, "page": page,
            "has_more": page * limit < total,
        }))
    finally:
        db.close()


@my_bp.route("/coins")
def my_coins():
    """代币余额 + 流水。"""
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    db = SessionLocal()
    try:
        user = db.get(User, g.user_id)
        balance = user.coins if user else 0
        q = db.query(CoinTransaction).filter(CoinTransaction.user_id == g.user_id)
        total = q.count()
        txs = (q.order_by(CoinTransaction.created_at.desc())
               .offset((page - 1) * limit).limit(limit).all())
        return jsonify(ok({
            "balance": balance,
            "transactions": [
                {"id": t.id, "amount": t.amount, "reason": t.reason,
                 "post_id": t.post_id,
                 "created_at": t.created_at.isoformat() if t.created_at else None}
                for t in txs],
            "total": total, "page": page,
            "has_more": page * limit < total,
        }))
    finally:
        db.close()
