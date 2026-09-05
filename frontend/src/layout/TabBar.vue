<template>
  <van-tabbar
    v-model="active"
    :fixed="true"
    :border="true"
    active-color="var(--color-primary)"
    inactive-color="#999999"
    @change="onChange"
  >
    <van-tabbar-item name="home" icon="home-o">首页</van-tabbar-item>
    <van-tabbar-item name="search" icon="search">搜索</van-tabbar-item>
    <van-tabbar-item name="publish" icon="edit">发布</van-tabbar-item>
    <van-tabbar-item name="notifications" icon="chat-o" :badge="unreadBadge">消息</van-tabbar-item>
    <van-tabbar-item name="my" icon="user-o">我的</van-tabbar-item>
  </van-tabbar>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'

const route = useRoute()
const router = useRouter()
const notificationStore = useNotificationStore()

// 路由路径 → Tab name 映射
const TAB_BY_PATH = {
  '/': 'home',
  '/search': 'search',
  '/publish': 'publish',
  '/notifications': 'notifications',
  '/my': 'my'
}

// 高亮当前路由对应的 Tab（单向绑定，实际跳转由 onChange 触发）
const active = computed(() => TAB_BY_PATH[route.path] || 'home')

// 消息未读红点：0 时不显示
const unreadBadge = computed(() =>
  notificationStore.unreadCount > 0 ? notificationStore.unreadCount : ''
)

function onChange(name) {
  const pathByTab = {
    home: '/',
    search: '/search',
    publish: '/publish',
    notifications: '/notifications',
    my: '/my'
  }
  const target = pathByTab[name]
  if (target && target !== route.path) {
    router.push(target)
  }
}
</script>
