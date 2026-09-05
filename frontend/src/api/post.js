import request from './request'

/**
 * 帖子 / 资讯相关接口（对齐 routes/main.py、routes/post.py）
 */

// 首页推荐流（协同过滤 + E-E 多目标打分；匿名时后端回退为最新）
export function getRecommend(params) {
  return request.get('/', { params })
}

// 最新：按发布时间倒序（参数 page / limit / zone 分区过滤）
export function getLatest(params) {
  return request.get('/latest', { params })
}

// 悬赏：type ∈ lost / secondhand / team，status ∈ unfinished / finished
export function getBounty(type = 'lost', params) {
  return request.get('/bounty', { params: { ...params, type } })
}

// 大事件：后端分组返回 [{event_id, title, nodes:[...]}]
export function getEvents(params) {
  return request.get('/events', { params })
}

// 单个大事件详情（纵向时间轴）
export function getEventDetail(id) {
  return request.get(`/events/${id}`)
}

// 分区元数据：36 内容分区 + 计数
export function getZones(params) {
  return request.get('/zones', { params })
}

// 帖子详情（含结构化评论 comments、like_count、liked）
export function getPostDetail(id) {
  return request.get(`/post/${id}`)
}

// 帖子评论列表（结构化 question/answer）
export function getPostComments(id, params) {
  return request.get(`/post/${id}/comments`, { params })
}

// 发布帖子（后端按 jieba 自动归类 zone + post_type）
export function publish(data) {
  return request.post('/publish', data)
}

// 发布评论（可选 reply_comment_id 楼中楼回复）
export function publishComment(data) {
  return request.post('/comment', data)
}

// 点赞（幂等）
export function likePost(postId) {
  return request.post('/like', { post_id: postId })
}

// —— 我的：我发 / 我回 / 我赞 / 金币 ——
export function getMyPosts(params) {
  return request.get('/my/posts', { params })
}

export function getMyReplies(params) {
  return request.get('/my/replies', { params })
}

export function getMyLikes(params) {
  return request.get('/my/likes', { params })
}

export function getMyCoins(params) {
  return request.get('/my/coins', { params })
}
