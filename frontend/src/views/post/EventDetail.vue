<template>
  <div class="page event-detail">
    <van-nav-bar title="大事件详情" left-arrow fixed placeholder @click-left="router.back()" />

    <!-- 骨架屏 -->
    <div v-if="!loaded && !error" class="event-detail__body">
      <van-skeleton title :row="6" />
    </div>

    <!-- 失败 -->
    <van-empty v-else-if="error" description="加载失败，请重试">
      <van-button size="small" type="primary" round @click="load">重新加载</van-button>
    </van-empty>

    <!-- 空 -->
    <van-empty v-else-if="!event" description="事件不存在或已过期" />

    <!-- 纵向时间轴：轴左、事件右 -->
    <template v-else>
      <div class="event-detail__head">
        <h1 class="event-detail__title">{{ event.title }}</h1>
        <div class="event-detail__count">共 {{ event.nodes.length }} 个节点</div>
      </div>

      <div class="v-timeline">
        <div v-for="n in event.nodes" :key="n.id" class="v-timeline__item">
          <div class="v-timeline__axis">
            <span class="v-timeline__dot"></span>
          </div>
          <div class="v-timeline__card">
            <div class="v-timeline__date">{{ n.date }}</div>
            <div class="v-timeline__title">{{ n.title }}</div>
            <div v-if="n.detail" class="v-timeline__detail">{{ n.detail }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getEventDetail } from '@/api'

defineOptions({ name: 'EventDetail' })

const route = useRoute()
const router = useRouter()
const eventId = route.params.id

const event = ref(null)
const loaded = ref(false)
const error = ref(false)

async function load() {
  error.value = false
  try {
    const res = await getEventDetail(eventId)
    const raw = res?.data?.event ?? null
    if (!raw) {
      event.value = null
      loaded.value = true
      return
    }
    event.value = {
      title: raw.title || '',
      nodes: (raw.nodes || []).map((n) => ({
        id: n.id,
        title: n.title || '',
        detail: n.detail || '',
        date: n.date || ''
      }))
    }
    loaded.value = true
  } catch (e) {
    error.value = true
  }
}
load()
</script>

<style scoped>
.event-detail {
  background: var(--color-page-bg);
  min-height: 100vh;
}

.event-detail__head {
  padding: 16px var(--page-margin) 4px;
}

.event-detail__title {
  margin: 0;
  font-size: var(--font-size-title);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.event-detail__count {
  margin-top: 6px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.v-timeline {
  padding: 12px var(--page-margin) 24px;
}

.v-timeline__item {
  display: flex;
}

.v-timeline__axis {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}

.v-timeline__dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(165, 42, 42, 0.18);
}

.v-timeline__axis::after {
  content: '';
  flex: 1;
  width: 2px;
  margin-top: 4px;
  background: var(--color-divider);
}

.v-timeline__item:last-child .v-timeline__axis::after {
  display: none;
}

.v-timeline__card {
  flex: 1;
  min-width: 0;
  margin: 0 0 12px 10px;
  padding: 12px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.v-timeline__date {
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.v-timeline__title {
  margin-top: 4px;
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.v-timeline__detail {
  margin-top: 6px;
  font-size: var(--font-size-body);
  line-height: 1.6;
  color: var(--color-text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
