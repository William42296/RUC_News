<template>
  <van-pull-refresh v-model="refreshing" @refresh="refresh">
    <!-- 骨架屏（首次加载） -->
    <template v-if="!loaded && !error">
      <div v-for="i in 3" :key="i" class="skeleton-card">
        <van-skeleton title :row="2" />
      </div>
    </template>

    <!-- 首次加载失败 -->
    <van-empty v-else-if="error && items.length === 0" description="加载失败，请重试">
      <van-button size="small" type="primary" round @click="loadFirst">重新加载</van-button>
    </van-empty>

    <!-- 列表 -->
    <template v-else>
      <div
        v-for="item in items"
        :key="item.id"
        class="list-item pressable"
        @click="onItemClick(item)"
      >
        <PostCard :post="item" />
      </div>

      <InfiniteSentinel
        :loading="loading"
        :finished="finished"
        finished-text="—— 没有更多了 ——"
        loading-text="加载中..."
        @load="loadMore"
      />
    </template>
  </van-pull-refresh>
</template>

<script setup>
import { useRouter } from 'vue-router'
import PostCard from '@/components/PostCard.vue'
import InfiniteSentinel from '@/components/InfiniteSentinel.vue'
import { usePagedList } from '@/composables/usePagedList'
import { normalizePost } from '@/utils/normalize'
import { trackPost } from '@/utils/tracker'
import { ACTION_TYPE } from '@/constants'

const props = defineProps({
  // (params) => Promise<res> 的数据请求函数
  fetcher: { type: Function, required: true },
  // 缓存键，空则不缓存
  cacheKey: { type: String, default: '' }
})

const router = useRouter()

const { items, loading, refreshing, finished, loaded, error, loadFirst, refresh, loadMore } =
  usePagedList({
    fetcher: props.fetcher,
    cacheKey: props.cacheKey,
    normalize: normalizePost
  })

function onItemClick(item) {
  if (!item.id) return
  trackPost(item.id, ACTION_TYPE.CLICK)
  router.push(`/post/${item.id}`)
}
</script>

<style scoped>
.skeleton-card {
  margin: 0 var(--page-margin) 12px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}
</style>
