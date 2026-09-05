<script setup>
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getNotifications, readAllNotifications } from '@/api'
import { usePagedList } from '@/composables/usePagedList'
import { normalizeNotification } from '@/utils/normalize'
import { useNotificationStore } from '@/stores/notification'
import { fromNow } from '@/utils/format'
import { CACHE_KEYS } from '@/constants'
import InfiniteSentinel from '@/components/InfiniteSentinel.vue'

defineOptions({ name: 'Notifications' })

const router = useRouter()
const notificationStore = useNotificationStore()

const { items, loading, refreshing, finished, loaded, error, loadFirst, refresh, loadMore } =
  usePagedList({
    fetcher: getNotifications,
    cacheKey: CACHE_KEYS.LIST_NOTIFICATIONS,
    normalize: normalizeNotification,
    // 未读红点以后端 Redis 计数 unread_count 为准
    onData: (res) => {
      const unread = res?.data?.unread_count
      if (typeof unread === 'number') notificationStore.setUnread(unread)
    }
  })

// —— 消息类型文案/配色：赞 / 回复 / 金币到账 ——
const TYPE_CLASS = {
  like: 'type-like',
  comment: 'type-comment',
  coin: 'type-coin'
}

function typeClass(type) {
  return TYPE_CLASS[type] || 'type-system'
}

// —— 点击单条：本地标记已读；有 post_id 则跳详情 ——
function onItemClick(item) {
  if (item && !item.read) item.read = true
  if (item?.postId) router.push(`/post/${item.postId}`)
}

// —— 一键已读 ——
async function onReadAll() {
  try {
    await readAllNotifications()
    items.value.forEach((i) => (i.read = true))
    notificationStore.clear()
    showToast('已全部标记为已读')
  } catch (e) {
    showToast('操作失败，请重试')
  }
}
</script>

<template>
  <div class="page notifications">
    <van-nav-bar title="消息" fixed placeholder>
      <template #right>
        <span class="read-all" @click="onReadAll">全部已读</span>
      </template>
    </van-nav-bar>

    <van-pull-refresh v-model="refreshing" @refresh="refresh">
      <!-- 骨架屏 -->
      <template v-if="!loaded && !error">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <van-skeleton title :row="1" />
        </div>
      </template>

      <!-- 加载失败 -->
      <van-empty v-else-if="error && items.length === 0" description="加载失败，请重试">
        <van-button size="small" type="primary" round @click="loadFirst">重新加载</van-button>
      </van-empty>

      <!-- 空态 -->
      <van-empty v-else-if="loaded && !items.length" description="暂无消息" />

      <!-- 列表 -->
      <template v-else>
        <div
          v-for="item in items"
          :key="item.id"
          class="msg pressable"
          @click="onItemClick(item)"
        >
          <span v-if="!item.read" class="msg__dot" />
          <div class="msg__main">
            <div class="msg__head">
              <span class="msg__type" :class="typeClass(item.type)">
                {{ item.typeText || '消息' }}
              </span>
              <span class="msg__time">{{ fromNow(item.time) }}</span>
            </div>
            <div class="msg__title">{{ item.content }}</div>
          </div>
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
  </div>
</template>

<style scoped>
.notifications {
  background: var(--color-page-bg);
}

.read-all {
  font-size: var(--font-size-body);
  color: var(--color-primary);
}

.skeleton-card {
  margin: 0 var(--page-margin) 12px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.msg {
  position: relative;
  display: flex;
  margin: 0 var(--page-margin) 10px;
  padding: 12px var(--page-margin) 12px 26px;
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.msg__dot {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-danger, #e95a4a);
}

.msg__main {
  flex: 1;
  min-width: 0;
}

.msg__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.msg__type {
  padding: 1px 10px;
  font-size: 11px;
  border-radius: 999px;
  line-height: 1.7;
}

.type-like {
  color: #b03a2e;
  background: rgba(176, 58, 46, 0.12);
}

.type-comment {
  color: #4a90d9;
  background: rgba(74, 144, 217, 0.12);
}

.type-coin {
  color: #c99335;
  background: rgba(201, 147, 53, 0.14);
}

.type-system {
  color: var(--color-text-secondary);
  background: var(--color-bg);
}

.msg__title {
  margin-top: 6px;
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  word-break: break-word;
}

.msg__time {
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}
</style>
