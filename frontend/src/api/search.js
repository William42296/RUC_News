import request from './request'

/**
 * 全文搜索
 * 返回字段可能包含 search_time_ms（搜索耗时），用于展示「搜索耗时 XX 毫秒」
 */
export function search(keyword, page = 1) {
  return request.get('/search', { params: { keyword, page } })
}
