<script setup>
import { computed, ref } from 'vue'
import { getRecommend, getLatest } from '@/api'
import { CACHE_KEYS } from '@/constants'
import PostList from '@/components/PostList.vue'
import EventTimeline from '@/components/EventTimeline.vue'
import ZonePanel from '@/components/ZonePanel.vue'
import BountyPanel from '@/components/BountyPanel.vue'

// keep-alive 依赖组件名缓存，必须显式声明
defineOptions({ name: 'Home' })

// 首页分类：最新 / 推荐 / 悬赏（悬赏令）/ 大事件 / 分区（37 分区）
const tabs = [
  { key: 'latest', label: '最新' },
  { key: 'recommend', label: '推荐' },
  { key: 'bounty', label: '悬赏' },
  { key: 'events', label: '大事件' },
  { key: 'zone', label: '分区' }
]

const activeTab = ref('latest')

const tabConfig = {
  recommend: { fetcher: getRecommend, cacheKey: CACHE_KEYS.LIST_HOT },
  latest: { fetcher: getLatest, cacheKey: CACHE_KEYS.LIST_LATEST }
}

const isEvents = computed(() => activeTab.value === 'events')
const isZone = computed(() => activeTab.value === 'zone')
const isBounty = computed(() => activeTab.value === 'bounty')
const current = computed(() => tabConfig[activeTab.value])
</script>

<template>
  <div class="page home">
    <van-nav-bar title="RUC News" fixed placeholder />

    <!-- 顶部横向可滚动标签栏（固定，offset 对齐导航栏高度 46px） -->
    <van-tabs v-model:active="activeTab" sticky scrollable :offset-top="46">
      <van-tab v-for="t in tabs" :key="t.key" :title="t.label" :name="t.key" />
    </van-tabs>

    <!-- 悬赏令 -->
    <BountyPanel v-if="isBounty" />
    <!-- 大事件：横向时间轴 -->
    <EventTimeline v-else-if="isEvents" />
    <!-- 分区：分区切换 + 帖子列表 -->
    <ZonePanel v-else-if="isZone" />
    <!-- 其余：卡片列表 -->
    <PostList v-else :key="activeTab" :fetcher="current.fetcher" :cache-key="current.cacheKey" />
  </div>
</template>

<style scoped>
.home {
  background: var(--color-bg);
}
</style>
