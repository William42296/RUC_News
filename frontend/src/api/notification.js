import request from './request'

/**
 * 消息通知相关接口
 */

// 消息列表
export function getNotifications(params) {
  return request.get('/notifications', { params })
}

// 一键已读
export function readAllNotifications() {
  return request.post('/read_all')
}
