"""集中配置：数据库、Redis、JWT、爬虫、推荐超参、分区、统一响应格式。"""
import os

import redis as redis_lib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- 数据库 ----------
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'ruc_news.db')}"

# ---------- Redis ----------
REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
# 显式连接池：复用连接、设上限，避免每请求新建连接（降延迟）
_redis_pool = redis_lib.ConnectionPool.from_url(
    REDIS_URL, decode_responses=True, max_connections=20)
redis_client = redis_lib.Redis(connection_pool=_redis_pool)

# Lua 原子缓存回填（EVALSHA 自动缓存脚本体）：命中即返回，未命中则 SET EX，
# 并发未命中时仅首个写者生效，防止重复写 / 缓存击穿。
GET_OR_SET = redis_client.register_script("""
local v = redis.call('GET', KEYS[1])
if v then return v end
redis.call('SET', KEYS[1], ARGV[1], 'EX', tonumber(ARGV[2]))
return ARGV[1]
""")

# ---------- JWT ----------
SECRET_KEY = os.environ.get("SECRET_KEY", "ruc-news-dev-secret-key-change-me-in-production-2026")
JWT_ALGO = "HS256"
JWT_EXPIRE_HOURS = 24 * 7

# ---------- 爬虫 ----------
CRAWLER_BASE_URL = "https://ys.qimiaoyuanfen.com"
CRAWLER_SESSION_FILE = os.path.join(BASE_DIR, "session.json")
SESSION_COOKIE_NAME = "ys_ysxy_sess"   # 真实抓包名；文档 ys7_ysxy_session 指同一 Session
AUTH_FAIL_CODE = "7001"
CRAWL_INTERVAL_SECONDS = 300           # 定时抓取间隔（秒）：满库后 5 分钟一次
BULK_CRAWL_THRESHOLD = 10000           # 数据库少于该条数时，全量抓取
CRAWLER_ENDPOINTS = {
    "latest": "/article/article/lists",
    "reply": "/article/article/lists2",
    "hot": "/article/article/datehot",
    "detail": "/article/article/info",
}
CRAWLER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 13; 22081212C Build/TKQ1.220829.002; wv) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/115.0.5790.166 "
        "Mobile Safari/537.36 XWEB/5715 MMWEBSDK/20230805 MMWEBID/8447 "
        "MicroMessenger/8.0.40.2440(0x28002858) WeChat/arm64 Weixin NetType/WIFI "
        "Language/zh_CN ABI/arm64 MiniProgramEnv/android"
    ),
    "Referer": "https://servicewechat.com/wxe23b94e06f71e89a/148/page-frame.html",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
}

# ---------- Redis 键名 ----------
KEY_POST_DETAIL = "post:detail:{}"
KEY_LIST_LATEST = "list:latest"
KEY_LIST_HOT = "list:hot"
KEY_MATRIX = "matrix:similarity"
KEY_NOTIF_UNREAD = "notification:unread:{}"
KEY_SEARCH = "search:res:{}:{}"

# ---------- 推荐超参 ----------
RECOMMEND_TOP_N = 10
MATRIX_TTL = 3600      # 相似度矩阵缓存 1 小时
SEARCH_TTL = 300       # 搜索缓存 5 分钟
DETAIL_TTL = 3600      # 帖子详情缓存 1 小时
HOT_SEARCH_N = 10      # 「大家都在搜」返回条数
EXPLORE_RATIO = 0.2    # 推荐中「探索」内容占比（E-E）
# 多目标打分权重：兴趣匹配 / 点击率 / 互动率
W_INTEREST = 0.5
W_CTR = 0.25
W_ENGAGE = 0.25

# ---------- 数据保留 ----------
DATA_RETENTION_DAYS = 30

# ---------- 内容分区（37 项去重「运动」→ 36 区） ----------
# 默认回落分区：资讯
ZONE_DEFAULT = 21

ZONE_NAMES = {
    1: "保研", 2: "考研", 3: "绩点", 4: "实习", 5: "考证", 6: "选课",
    7: "资料", 8: "社团", 9: "二手", 10: "问答", 11: "运动", 12: "课堂",
    13: "电影", 14: "电视剧", 15: "娱乐", 16: "音乐", 17: "舞蹈", 18: "绘画",
    19: "鬼畜", 20: "游戏", 21: "资讯", 22: "知识", 23: "AI", 24: "科技",
    25: "汽车", 26: "时尚", 27: "潮流", 28: "手工", 29: "美食", 30: "旅游",
    31: "三农", 32: "宠物", 33: "健康", 34: "vlog", 35: "兴趣", 36: "经验",
}

ZONE_KEYWORDS = {
    1: ["保研", "推免", "夏令营", "直博", "保送"],
    2: ["考研", "初试", "复试", "上岸", "研究生考试"],
    3: ["绩点", "GPA", "学分绩", "加权", "挂科"],
    4: ["实习", "offer", "内推", "简历", "面试", "秋招", "春招", "大厂"],
    5: ["考证", "证书", "四六级", "六级", "四级", "教资", "雅思", "托福", "计算机二级"],
    6: ["选课", "通识", "必修", "选修", "抢课", "排课"],
    7: ["资料", "笔记", "复习", "讲义", "真题", "电子书", "网课"],
    8: ["社团", "学生会", "招新", "协会"],
    9: ["二手", "转让", "出售", "求购", "闲置", "出手", "低价", "自提"],
    10: ["求助", "请问", "谁知道", "有没有人", "求问", "怎么"],
    11: ["运动", "跑步", "健身", "篮球", "足球", "羽毛球", "乒乓球", "游泳", "健身房"],
    12: ["上课", "课堂", "老师", "作业", "点名", "课件"],
    13: ["电影", "观影", "影评", "电影院", "上映"],
    14: ["电视剧", "追剧", "网剧", "美剧", "韩剧", "剧集"],
    15: ["娱乐", "明星", "八卦", "综艺", "演唱会"],
    16: ["音乐", "歌曲", "乐队", "专辑", "弹唱", "吉他", "钢琴"],
    17: ["舞蹈", "跳舞", "街舞", "民族舞", "舞蹈队"],
    18: ["绘画", "画画", "素描", "油画", "手绘", "板绘"],
    19: ["鬼畜", "恶搞", "剪辑", "二创", "调音"],
    20: ["游戏", "手游", "端游", "王者", "原神", "电竞", "开黑", "steam"],
    21: ["资讯", "新闻", "通知", "公告", "公示"],
    22: ["知识", "科普", "冷知识", "干货", "教程"],
    23: ["AI", "人工智能", "大模型", "ChatGPT", "机器学习", "深度学习"],
    24: ["科技", "数码", "手机", "电脑", "硬件", "软件", "编程"],
    25: ["汽车", "驾照", "开车", "新能源", "电动车"],
    26: ["时尚", "穿搭", "造型", "品牌"],
    27: ["潮流", "潮牌", "球鞋", "联名", "限量"],
    28: ["手工", "手作", "DIY", "编织", "陶艺"],
    29: ["美食", "吃饭", "餐厅", "外卖", "探店", "好吃", "食堂"],
    30: ["旅游", "旅行", "出游", "攻略", "景点", "酒店", "机票"],
    31: ["三农", "农村", "农业", "农民", "乡村"],
    32: ["宠物", "猫", "狗", "养猫", "养狗", "撸猫", "萌宠"],
    33: ["健康", "养生", "减肥", "饮食", "睡眠", "体检"],
    34: ["vlog", "日常", "记录", "短视频"],
    35: ["兴趣", "爱好", "同好", "交流"],
    36: ["经验", "分享", "心得", "经历", "避坑"],
}

# ---------- 悬赏 / 大事件 业务类型（与分区解耦） ----------
BOUNTY_TYPE_LABELS = {"team": "组队", "lost": "失物招领", "secondhand": "二手交易"}
POST_TYPE_KEYWORDS = {
    "lost": ["失物", "招领", "捡到", "拾到", "丢失", "遗失", "寻物", "失主", "掉了", "丢了"],
    "secondhand": ["二手", "转让", "出售", "求购", "闲置", "出手", "低价", "自提", "九成新"],
    "team": ["组队", "队友", "招募", "参赛", "组个队", "拼车", "拼单", "组队活动", "找搭子"],
}

# 源平台「公告/大事」类分区 → 大事件（post_type=event，供 /events 时间轴）
EVENT_SOURCE_CATEGORIES = {"反诈提醒", "放假", "新闻科研公示", "推免"}


def ok(data=None, message="success"):
    """统一成功响应。"""
    return {"code": 200, "data": data, "message": message}


def err(code, message):
    """统一失败响应。"""
    return {"code": code, "data": None, "message": message}
