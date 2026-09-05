<template>
  <van-pull-refresh v-model="refreshing" @refresh="refresh">
    <!-- 骨架屏 -->
    <template v-if="!loaded && !error">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <van-skeleton title :row="2" />
      </div>
    </template>

    <!-- 首次加载失败 -->
    <van-empty v-else-if="error && items.length === 0" description="加载失败，请重试">
      <van-button size="small" type="primary" round @click="loadFirst">重新加载</van-button>
    </van-empty>

    <!-- 时间轴 -->
    <template v-else>
      <div class="timeline">
        <div v-for="item in items" :key="item.id" class="timeline__item">
          <div class="timeline__axis">
            <span class="timeline__dot"></span>
          </div>
          <div class="timeline__card">
            <div class="timeline__time">{{ formatTime(item.time, 'YYYY-MM-DD') }}</div>
            <div class="timeline__title">{{ item.title }}</div>
            <div v-if="item.summary" class="timeline__summary ellipsis-2">{{ item.summary }}</div>
          </div>
        </div>
      </div>

      <van-list
        v-model:loading="loading"
        :finished="finished"
        :immediate-check="false"
        finished-text="—— 没有更多了 ——"
        loading-text="加载中..."
        @load="loadMore"
      />
    </template>
  </van-pull-refresh>
</template>

<script setup>
import { usePagedList } from '@/composables/usePagedList'
import { normalizePost } from '@/utils/normalize'
import { formatTime } from '@/utils/format'

const props = defineProps({
  fetcher: { type: Function, required: true },
  cacheKey: { type: String, default: '' }
})

const { items, loading, refreshing, finished, loaded, error, loadFirst, refresh, loadMore } =
  usePagedList({
    fetcher: props.fetcher,
    cacheKey: props.cacheKey,
    normalize: normalizePost,
    paginated: false // /events 后端一次性返回全部，非分页
  })
</script>

<style scoped>
.skeleton-card {
  margin: 0 var(--page-margin) 12px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.timeline {
  padding: 4px var(--page-margin) 0;
}

.timeline__item {
  display: flex;
}

.timeline__axis {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
  flex-shrink: 0;
}

.timeline__dot {
  width: 10px;
  height: 10px;
  margin-top: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(165, 42, 42, 0.18);
}

.timeline__axis::after {
  content: '';
  flex: 1;
  width: 2px;
  margin-top: 4px;
  background: var(--color-divider);
}

.timeline__item:last-child .timeline__axis::after {
  display: none;
}

.timeline__card {
  flex: 1;
  min-width: 0;
  margin: 0 0 12px 10px;
  padding: 12px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.timeline__time {
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.timeline__title {
  margin-top: 4px;
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.timeline__summary {
  margin-top: 6px;
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
}
</style>
