<template>
  <div class="event-timeline">
    <!-- 顶部小搜索栏 -->
    <van-search
      v-model="keyword"
      placeholder="搜索大事件"
      shape="round"
      background="transparent"
      @search="onSearch"
    />

    <!-- 骨架屏 -->
    <div v-if="!loaded && !error">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <van-skeleton title :row="2" />
      </div>
    </div>

    <!-- 失败 -->
    <van-empty v-else-if="error && events.length === 0" description="加载失败，请重试">
      <van-button size="small" type="primary" round @click="load">重新加载</van-button>
    </van-empty>

    <!-- 空态 -->
    <van-empty v-else-if="loaded && !events.length" description="暂无大事件" />

    <!-- 横向时间轴卡片 -->
    <template v-else>
      <div
        v-for="ev in events"
        :key="ev.eventId"
        class="event-card pressable"
        @click="onOpen(ev)"
      >
        <div class="event-card__head">
          <span class="event-card__title ellipsis">{{ ev.title }}</span>
          <span class="event-card__count">{{ ev.nodes.length }} 节点</span>
        </div>

        <div class="h-track">
          <div class="h-track__line"></div>
          <div
            v-for="(n, i) in ev.displayNodes"
            :key="n.id"
            class="h-node"
            :class="i % 2 === 0 ? 'h-node--above' : 'h-node--below'"
            :style="{ left: nodeLeft(i, ev.displayNodes.length) }"
          >
            <span class="h-node__dot"></span>
            <div class="h-node__text">
              <div class="h-node__date">{{ n.date }}</div>
              <div class="h-node__title ellipsis">{{ n.title }}</div>
            </div>
          </div>

          <!-- 超过 4 支：末端虚化提示 -->
          <div v-if="ev.hasMore" class="h-track__fade">···</div>
        </div>

        <div v-if="ev.hasMore" class="event-card__more">点击查看全部 {{ ev.nodes.length }} 个节点 →</div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getEvents } from '@/api'
import { CACHE_KEYS } from '@/constants'

defineOptions({ name: 'EventTimeline' })

const router = useRouter()

const keyword = ref('')
const events = ref([])
const loaded = ref(false)
const error = ref(false)
const MAX_NODES = 4

function onSearch(val) {
  const kw = String(val ?? '').trim()
  if (!kw) return
  router.push({ path: '/search', query: { q: kw } })
}

function nodeLeft(i, n) {
  const count = n || 1
  return `${((i + 0.5) / count) * 100}%`
}

function onOpen(ev) {
  router.push(`/event/${ev.eventId}`)
}

async function load() {
  error.value = false
  try {
    const res = await getEvents()
    const raw = res?.data?.events ?? res?.data ?? []
    events.value = (Array.isArray(raw) ? raw : []).map((ev) => ({
      eventId: ev.event_id ?? ev.id,
      title: ev.title || '',
      nodes: (ev.nodes || []).map((n) => ({
        id: n.id,
        title: n.title || '',
        detail: n.detail || '',
        date: n.date || ''
      })),
      displayNodes: (ev.nodes || []).slice(0, MAX_NODES).map((n) => ({
        id: n.id,
        title: n.title || '',
        detail: n.detail || '',
        date: n.date || ''
      })),
      hasMore: (ev.nodes || []).length > MAX_NODES
    }))
    loaded.value = true
  } catch (e) {
    error.value = true
  }
}
load()
</script>

<style scoped>
.event-timeline {
  background: var(--color-bg);
  padding-bottom: 12px;
}

.event-timeline :deep(.van-search) {
  padding: 8px var(--page-margin);
}

.skeleton-card {
  margin: 0 var(--page-margin) 12px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.event-card {
  margin: 0 var(--page-margin) 14px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.event-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.event-card__title {
  flex: 1;
  min-width: 0;
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.event-card__count {
  flex-shrink: 0;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.h-track {
  position: relative;
  height: 96px;
  margin-top: 14px;
}

.h-track__line {
  position: absolute;
  top: 48px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--color-divider);
}

.h-node {
  position: absolute;
  top: 48px;
  width: 25%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.h-node__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(165, 42, 42, 0.18);
}

.h-node__text {
  width: 100%;
  text-align: center;
}

.h-node--above {
  transform: translate(-50%, -34px);
}

.h-node--below {
  transform: translate(-50%, 12px);
}

.h-node__date {
  font-size: 11px;
  color: var(--color-text-secondary);
}

.h-node__title {
  margin-top: 2px;
  font-size: 12px;
  color: var(--color-text-primary);
}

.h-track__fade {
  position: absolute;
  top: 42px;
  right: 0;
  width: 42px;
  height: 16px;
  font-size: 18px;
  color: var(--color-text-secondary);
  background: linear-gradient(90deg, transparent, var(--color-card));
  text-align: right;
  line-height: 16px;
}

.event-card__more {
  margin-top: 6px;
  font-size: var(--font-size-aux);
  color: var(--color-primary);
  text-align: right;
}
</style>
