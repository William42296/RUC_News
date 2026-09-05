<template>
  <van-pull-refresh v-model="refreshing" @refresh="refresh">
    <!-- 骨架屏 -->
    <div v-if="!loaded && !error" class="bounty-grid">
      <div v-for="i in 4" :key="i" class="skeleton-card">
        <van-skeleton title :row="2" />
      </div>
    </div>

    <!-- 失败 -->
    <van-empty v-else-if="error && items.length === 0" description="加载失败，请重试">
      <van-button size="small" type="primary" round @click="loadFirst">重新加载</van-button>
    </van-empty>

    <!-- 空态 -->
    <van-empty v-else-if="loaded && !items.length" description="暂无悬赏任务" />

    <!-- 悬赏令网格 -->
    <template v-else>
      <div class="bounty-grid">
        <div
          v-for="item in items"
          :key="item.id"
          class="bounty-card pressable"
          @click="onOpen(item)"
        >
          <!-- 羊皮纸主体 -->
          <div class="parchment">
            <div class="parchment__task ellipsis-3">{{ item.title }}</div>

            <!-- 状态印章 -->
            <div class="seal" :class="item.status === 'finished' ? 'seal--done' : 'seal--todo'">
              {{ item.status === 'finished' ? '已完成' : '未完成' }}
            </div>

            <!-- 接单/领取按钮 -->
            <button
              type="button"
              class="accept-btn"
              @click.stop="onAccept(item)"
            >{{ item.status === 'finished' ? '查看' : '接单' }}</button>
          </div>

          <!-- 底部奖励 / 组队进度 -->
          <div class="bounty-card__footer">
            <template v-if="item.teamTotal > 0">
              <span class="progress-label">组队进度</span>
              <span class="progress-value">{{ item.teamCur }}/{{ item.teamTotal }}</span>
            </template>
            <template v-else>
              <span class="coin-icon">◈</span>
              <span class="reward-text">{{ item.reward || 0 }} 代币</span>
            </template>
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
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getBounty } from '@/api'
import { usePagedList } from '@/composables/usePagedList'
import { normalizePost } from '@/utils/normalize'
import { CACHE_KEYS, ACTION_TYPE } from '@/constants'
import { trackPost } from '@/utils/tracker'

const props = defineProps({
  type: { type: String, default: 'lost' },
  status: { type: String, default: 'unfinished' }
})

const router = useRouter()

const fetcher = (params) => getBounty(props.type, { ...params, status: props.status })
const cacheKey = `${CACHE_KEYS.LIST_BOUNTY}:${props.type}:${props.status}`

const { items, loading, refreshing, finished, loaded, error, loadFirst, refresh, loadMore } =
  usePagedList({ fetcher, cacheKey, normalize: normalizePost })

function onOpen(item) {
  if (!item.id) return
  trackPost(item.id, ACTION_TYPE.CLICK)
  router.push(`/post/${item.id}`)
}

function onAccept(item) {
  if (item.status === 'finished') {
    onOpen(item)
    return
  }
  showToast('已接单（演示）')
  trackPost(item.id, ACTION_TYPE.CLICK)
}
</script>

<style scoped>
.bounty-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  padding: 8px var(--page-margin) 0;
}

.skeleton-card {
  padding: 14px;
  background: var(--color-card);
  border-radius: var(--radius-card);
  aspect-ratio: 1;
}

.bounty-card {
  display: flex;
  flex-direction: column;
}

.parchment {
  position: relative;
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  padding: 16px 12px 44px;
  background:
    radial-gradient(circle at 30% 20%, rgba(160, 120, 60, 0.10), transparent 60%),
    radial-gradient(circle at 75% 85%, rgba(120, 80, 30, 0.14), transparent 55%),
    linear-gradient(135deg, #f3e4bd, #ead2a0 60%, #f0ddb3);
  border: 1px solid #c9a86a;
  border-radius: 10px;
  box-shadow:
    inset 0 0 18px rgba(139, 95, 30, 0.22),
    0 3px 8px rgba(139, 95, 30, 0.25);
}

.parchment__task {
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  font-size: 15px;
  line-height: 1.5;
  color: #5b3a12;
}

.seal {
  position: absolute;
  left: 12px;
  bottom: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 8px;
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  font-size: 13px;
  font-weight: 700;
  transform: rotate(-8deg);
  writing-mode: vertical-rl;
  letter-spacing: 2px;
  border: 3px double currentColor;
}

.seal--todo {
  color: #b03a2e;
  background: rgba(176, 58, 46, 0.08);
}

.seal--done {
  color: #3f7a3a;
  background: rgba(63, 122, 58, 0.08);
}

.accept-btn {
  position: absolute;
  right: 10px;
  bottom: 12px;
  padding: 6px 14px;
  font-size: var(--font-size-aux);
  color: #fff;
  background: linear-gradient(180deg, #b0472f, #8b1a1a);
  border: none;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(139, 26, 26, 0.4);
}

.bounty-card__footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 4px 0;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.coin-icon {
  color: var(--color-bounty);
}

.reward-text {
  color: var(--color-warning);
  font-weight: var(--font-weight-card-title);
}

.progress-value {
  color: var(--color-success);
  font-weight: var(--font-weight-card-title);
}
</style>
