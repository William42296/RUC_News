import { defineStore } from 'pinia'

/**
 * 全局 loading 计数：避免按钮重复提交 / 展示全局加载态
 * 设计文档 6.1 —— 通过 Pinia 维护全局 loading 计数
 */
export const useLoadingStore = defineStore('loading', {
  state: () => ({
    count: 0
  }),

  getters: {
    isLoading: (state) => state.count > 0
  },

  actions: {
    show() {
      this.count++
    },
    hide() {
      if (this.count > 0) this.count--
    }
  }
})
