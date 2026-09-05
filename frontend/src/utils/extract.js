/**
 * 后端响应结构的防御性解析（对齐 routes/*.py 返回结构）
 * 后端统一返回 { code, message, data }，列表字段：
 *   - 帖子列表：data.posts
 *   - 消息列表：data.notifications
 *   - 大事件：  data.events
 *   - 分区元数据：data.categories
 */

export function extractList(res) {
  const data = res?.data
  if (Array.isArray(data)) return data
  if (data && Array.isArray(data.posts)) return data.posts
  if (data && Array.isArray(data.notifications)) return data.notifications
  if (data && Array.isArray(data.events)) return data.events
  if (data && Array.isArray(data.categories)) return data.categories
  if (data && Array.isArray(data.zones)) return data.zones
  if (data && Array.isArray(data.replies)) return data.replies
  if (data && Array.isArray(data.hot)) return data.hot
  if (data && Array.isArray(data.list)) return data.list
  if (data && Array.isArray(data.items)) return data.items
  if (data && Array.isArray(data.results)) return data.results
  return []
}

export function extractHasMore(res, list, pageSize = 10) {
  const data = res?.data
  if (data && typeof data.has_more === 'boolean') return data.has_more
  if (data && typeof data.hasMore === 'boolean') return data.hasMore
  // 后端返回 total + page 时（如 /notifications 无 has_more），按 page*limit < total 判断
  if (data && data.total != null && data.page != null) {
    return data.page * pageSize < data.total
  }
  if (data && data.next != null && data.next !== '') return true
  if (data && typeof data.next_page === 'number') return data.next_page > 0
  // 兜底：本页返回满页则认为还有更多
  return list.length >= pageSize
}
