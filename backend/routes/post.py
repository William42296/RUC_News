"""发帖 & 评论 & 点赞 & 详情。"""
import json

from flask import Blueprint, g, jsonify, request

from config import (DETAIL_TTL, KEY_LIST_HOT, KEY_LIST_LATEST,
                    KEY_NOTIF_UNREAD, KEY_POST_DETAIL, err, ok, redis_client)
from models import (CoinTransaction, Comment, Like, Message, Post, SessionLocal,
                    User)
from utils import recommender

post_bp = Blueprint("post", __name__)

# 代币规则（金币到账 / 支出）
COIN_LIKE_GAIN = 1       # 被赞帖主到账
COIN_REPLY_GAIN = 1      # 回复者到账


def _credit_coins(db, user_id, amount, reason, post_id=None):
    """写代币账本并更新余额。"""
    if not user_id or amount == 0:
        return
    db.add(CoinTransaction(user_id=user_id, amount=amount, reason=reason,
                           post_id=post_id))
    user = db.get(User, user_id)
    if user:
        user.coins = (user.coins or 0) + amount


def _push_message(db, sender_id, receiver_id, post_id, content, mtype):
    """写站内消息（receiver 为 0 时跳过）。"""
    if not receiver_id:
        return
    db.add(Message(sender_id=sender_id, receiver_id=receiver_id, post_id=post_id,
                   content=content, type=mtype))


@post_bp.route("/publish", methods=["POST"])
def publish():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify(err(400, "title 和 content 不能为空")), 400
    if len(title) > 256 or len(content) > 5000:
        return jsonify(err(400, "标题或内容长度超限")), 400

    reward = int(data.get("reward") or 0)
    team_total = int(data.get("team_total") or 0)

    db = SessionLocal()
    post = Post(title=title, content=content, owner_id=g.user_id,
                reward=max(0, reward), team_total=max(0, team_total),
                team_cur=0, status="unfinished")
    db.add(post)
    db.commit()
    post_id = post.id
    db.close()

    zone, ptype = recommender.index_post(post_id, title, content)
    redis_client.delete(KEY_LIST_HOT, KEY_LIST_LATEST)
    return jsonify(ok({"post_id": post_id, "zone": zone, "post_type": ptype}))


@post_bp.route("/post/<int:pid>")
def detail(pid):
    key = KEY_POST_DETAIL.format(pid)
    cached = redis_client.get(key)
    if cached:
        return jsonify(json.loads(cached))
    db = SessionLocal()
    try:
        post = db.get(Post, pid)
        if not post:
            return jsonify(err(404, "帖子不存在")), 404
        comments = _structured_comments(db, pid)
        like_count = db.query(Like).filter(Like.post_id == pid).count()
        liked = False
        if getattr(g, "user_id", None):
            liked = (db.query(Like).filter(Like.post_id == pid,
                                           Like.user_id == g.user_id).first()
                     is not None)
        resp = ok({
            "id": post.id, "title": post.title, "content": post.content,
            "zone": post.zone, "post_type": post.post_type,
            "status": post.status, "reward": post.reward,
            "team_cur": post.team_cur, "team_total": post.team_total,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "comments": comments, "comments_count": len(comments),
            "like_count": like_count, "liked": liked,
        })
    finally:
        db.close()
    redis_client.set(key, json.dumps(resp), ex=DETAIL_TTL)
    return jsonify(resp)


@post_bp.route("/post/<int:pid>/comments")
def comments(pid):
    db = SessionLocal()
    try:
        if not db.get(Post, pid):
            return jsonify(err(404, "帖子不存在")), 404
        return jsonify(ok({"comments": _structured_comments(db, pid)}))
    finally:
        db.close()


def _structured_comments(db, pid):
    """结构化评论：question/answer 楼中楼（回溯父评论 detail）。"""
    rows = (db.query(Comment).filter(Comment.post_id == pid)
            .order_by(Comment.created_at.asc()).all())
    by_id = {c.id: c for c in rows}
    out = []
    for c in rows:
        question = "无（初始帖子评论）"
        if c.reply_comment_id and c.reply_comment_id in by_id:
            question = by_id[c.reply_comment_id].content
        out.append({
            "id": c.id, "content": c.content, "question": question,
            "reply_comment_id": c.reply_comment_id, "user_id": c.user_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return out


@post_bp.route("/comment", methods=["POST"])
def comment():
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    content = (data.get("content") or "").strip()
    reply_comment_id = int(data.get("reply_comment_id") or 0)
    if not post_id or not content:
        return jsonify(err(400, "post_id 和 content 不能为空")), 400

    db = SessionLocal()
    try:
        post = db.get(Post, post_id)
        if not post:
            return jsonify(err(404, "帖子不存在")), 404
        c = Comment(post_id=post_id, user_id=g.user_id, content=content,
                    reply_comment_id=reply_comment_id)
        db.add(c)
        db.flush()
        comment_id = c.id
        author = post.owner_id

        _push_message(db, g.user_id, author, post_id, content, "comment")
        _credit_coins(db, g.user_id, COIN_REPLY_GAIN, "reply", post_id)
        _push_message(db, 0, g.user_id, post_id, f"回复获得 {COIN_REPLY_GAIN} 代币", "coin")
        db.commit()
    finally:
        db.close()

    if author:
        redis_client.incr(KEY_NOTIF_UNREAD.format(author))
    redis_client.delete(KEY_POST_DETAIL.format(post_id))
    return jsonify(ok({"comment_id": comment_id}))


@post_bp.route("/like", methods=["POST"])
def like():
    data = request.get_json(silent=True) or {}
    post_id = data.get("post_id")
    if not post_id:
        return jsonify(err(400, "post_id 不能为空")), 400

    db = SessionLocal()
    try:
        post = db.get(Post, post_id)
        if not post:
            return jsonify(err(404, "帖子不存在")), 404

        existing = db.query(Like).filter(Like.post_id == post_id,
                                         Like.user_id == g.user_id).first()
        if existing:
            like_count = db.query(Like).filter(Like.post_id == post_id).count()
            return jsonify(ok({"liked": True, "already": True,
                               "like_count": like_count}))

        db.add(Like(user_id=g.user_id, post_id=post_id))
        author = post.owner_id
        if author and author != g.user_id:
            _credit_coins(db, author, COIN_LIKE_GAIN, "like", post_id)
            _push_message(db, g.user_id, author, post_id, "赞了你的帖子", "like")
            _push_message(db, 0, author, post_id, f"被赞获得 {COIN_LIKE_GAIN} 代币", "coin")
        db.commit()
        like_count = db.query(Like).filter(Like.post_id == post_id).count()
    finally:
        db.close()

    if author and author != g.user_id:
        redis_client.incr(KEY_NOTIF_UNREAD.format(author))
    redis_client.delete(KEY_POST_DETAIL.format(post_id))
    return jsonify(ok({"liked": True, "like_count": like_count}))
