import { reportFeedback } from '@/api'

/**
 * 全局行为埋点（对齐后端 /my/feedback）
 * 后端 UserAction 仅记录「帖子 + 行为」，action_type ∈ click | view，
 * 用于推荐矩阵更新（recommender.update_matrix），故埋点粒度为帖子级。
 * 上报走 reportFeedback（silent，失败不打扰用户）。
 */
export function trackPost(postId, actionType) {
  if (!postId) return
  reportFeedback({ post_id: postId, action_type: actionType }).catch(() => {})
}
