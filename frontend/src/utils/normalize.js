/**
 * 后端字段名 → 前端统一结构 的映射层（对齐 config.py / models.py / routes/*.py）
 */

import { CATEGORY_NAMES } from '@/constants'

function pick(obj, keys) {
  for (const key of keys) {
    if (obj && obj[key] !== undefined && obj[key] !== null && obj[key] !== '') {
      return obj[key]
    }
  }
  return undefined
}

/**
 * 将任意结构的帖子数据，归一化为卡片 / 详情 / 时间轴所需的结构
 * @param {Object} raw 后端原始数据项
 */
export function normalizePost(raw) {
  if (!raw) return null
  const content = pick(raw, ['content', 'body', 'text', 'detail']) || ''
  const category = pick(raw, ['category'])
  return {
    id: pick(raw, ['id', 'post_id', 'pid']),
    title: pick(raw, ['title', 'subject']) || '',
    // 后端列表接口的 content 已截断为 100 字，直接作为卡片摘要；详情页用 content 完整正文
    summary: pick(raw, ['summary', 'excerpt', 'description']) || content.slice(0, 100),
    content,
    category,
    categoryName: pick(raw, ['category_name', 'categoryName']) || CATEGORY_NAMES[category] || '',
    postType: pick(raw, ['post_type', 'postType']) || '',
    time: pick(raw, ['created_at', 'create_time', 'publish_time', 'published_at', 'date', 'time']),
    commentCount: Number(
      pick(raw, ['comments_count', 'comment_count', 'commentCount', 'reply_count', 'comments']) || 0
    ),
    raw
  }
}

/**
 * 归一化评论结构（详情页）
 * 注：后端目前仅 POST /comment 写入、详情返回 comments_count，暂无评论列表接口。
 */
export function normalizeComment(raw) {
  if (!raw) return null
  return {
    id: pick(raw, ['id', 'comment_id', 'cid']),
    content: pick(raw, ['content', 'body', 'text']) || '',
    author: pick(raw, ['author', 'nickname', 'user_name', 'name', 'username']) || '',
    time: pick(raw, ['created_at', 'create_time', 'time'])
  }
}

/**
 * 归一化消息结构（消息页，对齐 routes/info.py 的 notifications 字段）
 * @param {Object} raw 后端原始消息数据
 */
export function normalizeNotification(raw) {
  if (!raw) return null
  return {
    id: pick(raw, ['id', 'notification_id', 'nid']),
    type: pick(raw, ['type', 'category', 'action_type']) || '',
    title: pick(raw, ['title', 'subject']) || '',
    content: pick(raw, ['content', 'body', 'text', 'message']) || '',
    time: pick(raw, ['created_at', 'create_time', 'time']),
    read: Boolean(pick(raw, ['read', 'is_read', 'read_flag'])),
    postId: pick(raw, ['post_id', 'pid', 'target_id', 'ref_id'])
  }
}
