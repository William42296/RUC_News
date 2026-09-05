import { createRouter, createWebHashHistory } from 'vue-router'
import { showToast } from 'vant'
import { useUserStore } from '@/stores/user'

/**
 * 路由配置（Hash 模式，适配微信浏览器历史记录）
 *
 * 权限说明：
 * - 设计文档 6.1 / 5.3 明确「发布」需登录拦截；「消息」「帖子详情」涉及评论互动，一并要求登录。
 * - 首页 / 搜索 / 我的 保持可访问（我的页内含「未登录 → 点击登录」态）。
 * - 如需「所有页面强制登录」，将下方 meta.requiresAuth 全设为 true 即可（守卫逻辑已统一）。
 */
const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页', tab: true }
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/Search.vue'),
    meta: { title: '搜索', tab: true }
  },
  {
    path: '/publish',
    name: 'publish',
    component: () => import('@/views/Publish.vue'),
    meta: { title: '发布', tab: true, requiresAuth: true }
  },
  {
    path: '/notifications',
    name: 'notifications',
    component: () => import('@/views/Notifications.vue'),
    meta: { title: '消息', tab: true, requiresAuth: true }
  },
  {
    path: '/my',
    name: 'my',
    component: () => import('@/views/My.vue'),
    meta: { title: '我的', tab: true }
  },
  {
    path: '/post/:id',
    name: 'post-detail',
    component: () => import('@/views/post/detail.vue'),
    meta: { title: '帖子详情', requiresAuth: true }
  },
  {
    path: '/event/:id',
    name: 'event-detail',
    component: () => import('@/views/post/EventDetail.vue'),
    meta: { title: '大事件详情' }
  },
  // 兜底重定向
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// —— 全局前置守卫：权限拦截 ——
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    showToast('请先登录')
    next({ path: '/my', query: { redirect: to.fullPath } })
    return
  }
  next()
})

// —— 全局后置守卫：更新标题 ——
router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · RUC News` : 'RUC News'
})

export default router
