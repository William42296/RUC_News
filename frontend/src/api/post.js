import request from './request'

/**
 * 帖子 / 资讯相关接口（对齐 routes/main.py、routes/post.py）
 */

// 首页推荐流（协同过滤；匿名时后端回退为最新）
export function getRecommend(params) {
  return request.get('/', { params })
}

// 最新：按发布时间倒序（参数 page / limit）
export function getLatest(params) {
  return request.get('/latest', { params })
}

// 悬赏：post_type ∈ lost / secondhand / team
export function getBounty(type = 'lost', params) {
  return request.get('/bounty', { params: { ...params, type } })
}

// 大事件：post_type = event（后端非分页，返回全部；可选 year/month 过滤）
export function getEvents(params) {
  return request.get('/events', { params })
}

// 帖子详情（返回正文 + comments_count；评论列表后端暂未提供）
export function getPostDetail(id) {
  return request.get(`/post/${id}`)
}

// 发布帖子：后端按特征词自动归类（category）并入库
export function publish(data) {
  return request.post('/publish', data)
}

// 发布评论
export function publishComment(data) {
  return request.post('/comment', data)
}
