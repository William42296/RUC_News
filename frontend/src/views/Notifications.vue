<script setup>
import { showToast } from 'vant'
import { getNotifications, readAllNotifications } from '@/api'
import { usePagedList } from '@/composables/usePagedList'
import { normalizeNotification } from '@/utils/normalize'
import { useNotificationStore } from '@/stores/notification'
import { fromNow } from '@/utils/format'
import { CACHE_KEYS } from '@/constants'

defineOptions({ name: 'Notifications' })

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

// —— 点击单条：本地标记已读（后端暂无单条已读接口，消息不含 post_id 故不跳转）——
function onItemClick(item) {
  if (item && !item.read) item.read = true
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
            <div class="msg__title">{{ item.content }}</div>
            <div class="msg__time">{{ fromNow(item.time) }}</div>
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

.msg__title {
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  word-break: break-word;
}

.msg__time {
  margin-top: 6px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}
</style>
