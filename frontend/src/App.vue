<template>
  <div class="app">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <keep-alive include="Home,Search">
          <component :is="Component" :key="route.path" />
        </keep-alive>
      </transition>
    </router-view>

    <!-- 底部 Tab 导航：仅带 tab 标记的页面展示 -->
    <TabBar v-if="showTabBar" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TabBar from '@/layout/TabBar.vue'

const route = useRoute()

// 只有首页/搜索/发布/消息/我的 五个 Tab 页显示底部导航
const showTabBar = computed(() => route.meta.tab === true)
</script>

<style scoped>
.app {
  min-height: 100vh;
}
</style>
