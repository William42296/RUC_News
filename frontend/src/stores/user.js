import { defineStore } from 'pinia'
import { getStorage, setStorage, removeStorage } from '@/utils/storage'
import { TOKEN_KEY, USER_KEY } from '@/constants'

/**
 * 用户状态：持久化 Token 与用户信息
 */
export const useUserStore = defineStore('user', {
  state: () => ({
    token: getStorage(TOKEN_KEY, ''),
    userInfo: getStorage(USER_KEY, null)
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    nickname: (state) => state.userInfo?.nickname || state.userInfo?.name || '',
    avatar: (state) => state.userInfo?.avatar || ''
  },

  actions: {
    setToken(token) {
      this.token = token
      setStorage(TOKEN_KEY, token)
    },

    setUserInfo(info) {
      this.userInfo = info
      setStorage(USER_KEY, info)
    },

    clearUser() {
      this.token = ''
      this.userInfo = null
      removeStorage(TOKEN_KEY)
      removeStorage(USER_KEY)
    }
  }
})
