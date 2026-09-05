import request from './request'

/**
 * 登录 / 用户相关接口（对齐 routes/my.py）
 */

// 登录：POST /my/login（后端校验 crawler session 后签发 JWT，无需 body）
export function login() {
  return request.post('/my/login', {}, { skipAuth: true })
}
