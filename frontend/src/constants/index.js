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
  SEARCH_RES: 'search:res',   // 实际键 search:res:{keyword}:{page}
  POST_DETAIL: 'post:detail', // 实际键 post:detail:{id}
  SEARCH_HISTORY: 'search:history',
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
  EVENTS: 'events'
}

// —— 发帖字段上限（对齐后端 routes/post.py 校验）——
export const POST_LIMIT = {
  TITLE: 256,    // 标题最大字数
  CONTENT: 5000  // 内容最大字数
}

// —— 业务分区名（对齐后端 config.py CATEGORY_NAMES，category 为 1-4 整数）——
export const CATEGORY_NAMES = {
  1: '综合',
  2: '二手交易',
  3: '失物招领',
  4: '组队活动'
}

// —— 搜索历史条数上限 ——
export const SEARCH_HISTORY_MAX = 5

// —— 埋点行为类型 ——
export const ACTION_TYPE = {
  CLICK: 'click',
  VIEW: 'view'
}
