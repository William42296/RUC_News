import axios from 'axios'
import { showToast, showDialog } from 'vant'
import { getStorage, removeStorage } from '@/utils/storage'
import { TOKEN_KEY } from '@/constants'
import { useUserStore } from '@/stores/user'
import router from '@/router'

/**
 * Axios 统一封装（对应设计文档 6.1）
 * - 请求拦截：自动注入 Authorization: Bearer {token}
 * - 响应拦截：code === 401 清 Token 跳登录；code !== 200 全局 Toast
 * - 支持 config.silent：静默请求（轮询/埋点）不弹 Toast
 * - 支持 config.skipAuth：跳过 Token 注入（登录接口）
 */
const request = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL || '/api',
  timeout: 10000
})

// —— 请求拦截 ——
request.interceptors.request.use(
  (config) => {
    if (!config.skipAuth) {
      const token = getStorage(TOKEN_KEY)
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// —— 响应拦截 ——
request.interceptors.response.use(
  (response) => {
    const res = response.data

    // 后端统一返回 { code, message, data }；也兼容直接返回 data 的情况
    const code = res?.code ?? 200

    if (code === 401) {
      handleUnauthorized()
      return Promise.reject(res)
    }

    if (code !== 200 && code !== 0) {
      if (!response.config.silent) {
        showToast(res?.message || '请求失败')
      }
      return Promise.reject(res)
    }

    return res
  },
  (error) => {
    // HTTP 层错误（网络异常 / 超时 / 业务错误码）
    if (error.response?.status === 401) {
      if (error.config?.skipAuth) {
        // 登录接口返回 401 = Session 无效，而非 Token 过期
        if (!error.config?.silent) showToast(error.response?.data?.message || '登录失败')
      } else {
        handleUnauthorized()
      }
    } else if (!error.config?.silent) {
      showToast(error.response?.data?.message || '网络异常，请稍后重试')
    }
    return Promise.reject(error)
  }
)

let unauthorizedHandling = false

function handleUnauthorized() {
  // 防止并发多个 401 时重复弹窗
  if (unauthorizedHandling) return
  unauthorizedHandling = true

  removeStorage(TOKEN_KEY)
  const userStore = useUserStore()
  userStore.clearUser()

  showDialog({
    title: '提示',
    message: '登录已过期，请重新登录'
  })
    .then(() => {
      router.replace('/my')
    })
    .catch(() => {
      router.replace('/my')
    })
    .finally(() => {
      unauthorizedHandling = false
    })
}

export default request
