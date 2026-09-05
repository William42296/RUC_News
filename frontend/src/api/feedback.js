import request from './request'

/**
 * 行为上报（对齐 routes/my.py 的 /my/feedback）
 * - 仅接受 { post_id, action_type }，action_type ∈ click | view
 * - silent：上报失败不打扰用户
 */
export function reportFeedback(payload) {
  return request.post('/my/feedback', payload, { silent: true })
}
