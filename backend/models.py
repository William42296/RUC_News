"""SQLAlchemy ORM 数据模型。"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, create_engine, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from config import DATABASE_URL, ZONE_DEFAULT


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    openid: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(64), default="")
    preferences: Mapped[str] = mapped_column(Text, default="{}")  # JSON 字符串
    coins: Mapped[int] = mapped_column(Integer, default=0)         # 代币余额（由账本聚合）


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # 源站帖子 id
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[int] = mapped_column(Integer, default=1)             # 业务分区（过渡，逐步被 zone 取代）
    zone: Mapped[int] = mapped_column(Integer, default=ZONE_DEFAULT)      # 内容分区 1-36（jieba 归类）
    source_category_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 源站真实 category_id
    source_category_name: Mapped[str] = mapped_column(String(64), default="")       # 源站真实版块名
    hot: Mapped[int] = mapped_column(Integer, default=0)                  # 热度
    post_type: Mapped[str] = mapped_column(String(16), default="normal")  # normal/lost/secondhand/team/event
    status: Mapped[str] = mapped_column(String(16), default="unfinished")  # unfinished/finished（悬赏）
    reward: Mapped[int] = mapped_column(Integer, default=0)               # 悬赏奖励代币数
    team_cur: Mapped[int] = mapped_column(Integer, default=0)             # 组队当前人数
    team_total: Mapped[int] = mapped_column(Integer, default=0)           # 组队目标人数
    source_url: Mapped[str] = mapped_column(String(512), default="")
    owner_id: Mapped[int] = mapped_column(Integer, default=0)             # 0 = 抓取帖
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, default=0)              # 0 = 抓取
    content: Mapped[str] = mapped_column(Text, default="")
    reply_comment_id: Mapped[int] = mapped_column(Integer, default=0)     # 0 = 顶层评论，否则回溯父评论
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 源站评论 id（去重）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_like_user_post"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CoinTransaction(Base):
    __tablename__ = "coin_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)               # 带符号金额（+收入 / -支出）
    reason: Mapped[str] = mapped_column(String(16), default="other")      # like/reply/bounty
    post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class UserAction(Base):
    __tablename__ = "user_actions"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    post_id: Mapped[int] = mapped_column(Integer, index=True)
    action_type: Mapped[str] = mapped_column(String(16), default="click")  # click/view
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(Integer, default=0)
    receiver_id: Mapped[int] = mapped_column(Integer, index=True)
    post_id: Mapped[int | None] = mapped_column(Integer, nullable=True)    # 评论/点赞关联的帖子
    content: Mapped[str] = mapped_column(Text, default="")
    type: Mapped[str] = mapped_column(String(16), default="system")        # comment/like/coin/system
    is_read: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def _migrate():
    """旧库兼容：为新字段/新表做 ALTER TABLE 兜底（新库由 create_all 直接建）。"""
    from sqlalchemy import text

    columns = {
        "posts": [
            ("zone", "INTEGER DEFAULT %d" % ZONE_DEFAULT),
            ("status", "VARCHAR(16) DEFAULT 'unfinished'"),
            ("reward", "INTEGER DEFAULT 0"),
            ("team_cur", "INTEGER DEFAULT 0"),
            ("team_total", "INTEGER DEFAULT 0"),
        ],
        "users": [("coins", "INTEGER DEFAULT 0")],
    }
    with engine.begin() as conn:
        for table, cols in columns.items():
            existing = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))}
            for name, ddl in cols:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def init_db():
    _migrate()
    Base.metadata.create_all(engine)
