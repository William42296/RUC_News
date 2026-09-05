/**
 * 全局常量定义
 */

// —— 本地存储键（storage 工具会自动加 ruc: 前缀）——
export const TOKEN_KEY = 'token'
export const USER_KEY = 'user'
export const UNREAD_KEY = 'unread'

// —— 缓存键（对应设计文档 6.2 关键缓存键值）——
export const CACHE_KEYS = {
  LIST_LATEST: 'list:latest',
  LIST_HOT: 'list:hot',
  LIST_BOUNTY: 'list:bounty',
  LIST_EVENTS: 'list:events',
  LIST_NOTIFICATIONS: 'list:notifications',
  LIST_ZONES: 'list:zones',
  LIST_MY_POSTS: 'list:my:posts',
  LIST_MY_REPLIES: 'list:my:replies',
  LIST_MY_LIKES: 'list:my:likes',
  SEARCH_RES: 'search:res',   // 实际键 search:res:{keyword}:{page}
  SEARCH_HOT: 'search:hot',
  POST_DETAIL: 'post:detail', // 实际键 post:detail:{id}
  SEARCH_HISTORY: 'search:history',
  SEARCH_HOT_HIDDEN: 'search:hot:hidden',
  DRAFT: 'draft'
}

// —— 缓存有效期（毫秒）——
export const CACHE_TTL = {
  LIST: 5 * 60 * 1000,   // 5 分钟
  SEARCH: 5 * 60 * 1000,
  DETAIL: 5 * 60 * 1000
}

// —— 首页分类 ——
export const CATEGORY = {
  RECOMMEND: 'recommend',
  LATEST: 'latest',
  BOUNTY: 'bounty',
  EVENTS: 'events',
  ZONE: 'zone'
}

// —— 发帖字段上限（对齐后端 routes/post.py 校验）——
export const POST_LIMIT = {
  TITLE: 256,    // 标题最大字数
  CONTENT: 5000  // 内容最大字数
}

// —— 内容分区（对齐后端 config.py ZONE_NAMES，36 项）——
export const ZONES = [
  { id: 1, name: '保研' }, { id: 2, name: '考研' }, { id: 3, name: '绩点' },
  { id: 4, name: '实习' }, { id: 5, name: '考证' }, { id: 6, name: '选课' },
  { id: 7, name: '资料' }, { id: 8, name: '社团' }, { id: 9, name: '二手' },
  { id: 10, name: '问答' }, { id: 11, name: '运动' }, { id: 12, name: '课堂' },
  { id: 13, name: '电影' }, { id: 14, name: '电视剧' }, { id: 15, name: '娱乐' },
  { id: 16, name: '音乐' }, { id: 17, name: '舞蹈' }, { id: 18, name: '绘画' },
  { id: 19, name: '鬼畜' }, { id: 20, name: '游戏' }, { id: 21, name: '资讯' },
  { id: 22, name: '知识' }, { id: 23, name: 'AI' }, { id: 24, name: '科技' },
  { id: 25, name: '汽车' }, { id: 26, name: '时尚' }, { id: 27, name: '潮流' },
  { id: 28, name: '手工' }, { id: 29, name: '美食' }, { id: 30, name: '旅游' },
  { id: 31, name: '三农' }, { id: 32, name: '宠物' }, { id: 33, name: '健康' },
  { id: 34, name: 'vlog' }, { id: 35, name: '兴趣' }, { id: 36, name: '经验' }
]

export const ZONE_NAMES = Object.fromEntries(ZONES.map((z) => [z.id, z.name]))

// —— 悬赏三大业务分类（对齐后端 BOUNTY_TYPE_LABELS）——
export const BOUNTY_TYPES = [
  { key: 'team', label: '组队' },
  { key: 'lost', label: '事务招领' },
  { key: 'secondhand', label: '二手交易' }
]

export const BOUNTY_STATUS = [
  { key: 'unfinished', label: '未完成' },
  { key: 'finished', label: '已完成' }
]

// —— 搜索历史条数上限 ——
export const SEARCH_HISTORY_MAX = 5

// —— 埋点行为类型 ——
export const ACTION_TYPE = {
  CLICK: 'click',
  VIEW: 'view'
}
