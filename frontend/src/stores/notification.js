import { defineStore } from 'pinia'
import { getStorage, setStorage } from '@/utils/storage'
import { UNREAD_KEY } from '@/constants'

/**
 * 消息通知状态：维护未读计数，驱动底部 Tab 红点
 */
export const useNotificationStore = defineStore('notification', {
  state: () => ({
    unreadCount: getStorage(UNREAD_KEY, 0)
  }),

  actions: {
    setUnread(count) {
      this.unreadCount = count
      setStorage(UNREAD_KEY, count)
    },
    clear() {
      this.unreadCount = 0
      setStorage(UNREAD_KEY, 0)
    }
  }
})
