import request from './request'

/**
 * 全文搜索 + 热门搜索
 */

// 全文搜索（可选 post_type 快捷分类过滤：lost / secondhand / team）
export function search(keyword, page = 1, postType = '') {
  const params = { keyword, page }
  if (postType) params.post_type = postType
  return request.get('/search', { params })
}

// 大家都在搜：点击量最高的帖子（offset 用于「换一换」）
export function getSearchHot(params) {
  return request.get('/search/hot', { params })
}
