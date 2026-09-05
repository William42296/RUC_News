<template>
  <!-- 撕裂纸边沿滤镜：feTurbulence + feDisplacementMap 生成不规则毛边 -->
  <svg class="torn-filter" aria-hidden="true" focusable="false">
    <defs>
      <filter id="paper-torn" x="-15%" y="-15%" width="130%" height="130%">
        <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" result="noise" />
        <feDisplacementMap in="SourceGraphic" in2="noise" scale="9" xChannelSelector="R" yChannelSelector="G" />
      </filter>
    </defs>
  </svg>

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
            <!-- 撕裂边沿纸层（滤镜位移，文字层不受影响） -->
            <div class="parchment__paper" aria-hidden="true"></div>

            <div class="parchment__task ellipsis-3">{{ item.title }}</div>

            <!-- 状态印章（圆形双环） -->
            <div class="seal" :class="item.status === 'finished' ? 'seal--done' : 'seal--todo'">
              <span
                v-for="(ch, i) in (item.status === 'finished' ? '已完成' : '未完成')"
                :key="i"
              >{{ ch }}</span>
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
import { showToast } from 'vant'
import { getBounty } from '@/api'
import { usePagedList } from '@/composables/usePagedList'
import { normalizePost } from '@/utils/normalize'
import { CACHE_KEYS, ACTION_TYPE } from '@/constants'
import { trackPost } from '@/utils/tracker'
import InfiniteSentinel from '@/components/InfiniteSentinel.vue'

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
  grid-template-columns: repeat(auto-fill, 160px);
  gap: 12px;
  padding: 8px var(--page-margin) 0;
  justify-content: center;
}

.skeleton-card {
  width: 160px;
  height: 160px;
  box-sizing: border-box;
  padding: 14px;
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.bounty-card {
  display: flex;
  flex-direction: column;
  width: 160px;
  height: 160px;
  box-sizing: border-box;
  overflow: hidden;
}

.torn-filter {
  position: absolute;
  width: 0;
  height: 0;
  overflow: hidden;
}

.parchment {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 18px 16px 44px;
}

/* 撕裂边沿纸层：纹理/毛边由滤镜位移产生，文字层与其分离 */
.parchment__paper {
  position: absolute;
  inset: 3px;
  background:
    radial-gradient(circle at 30% 20%, rgba(160, 120, 60, 0.10), transparent 60%),
    radial-gradient(circle at 75% 85%, rgba(120, 80, 30, 0.14), transparent 55%),
    linear-gradient(135deg, #f3e4bd, #ead2a0 60%, #f0ddb3);
  border: 1px solid #c9a86a;
  box-shadow: inset 0 0 18px rgba(139, 95, 30, 0.22);
  filter: url(#paper-torn) drop-shadow(0 3px 6px rgba(139, 95, 30, 0.35));
}

.parchment__task {
  position: relative;
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  font-size: 16px;
  line-height: 1.5;
  color: #5b3a12;
}

.seal {
  position: absolute;
  left: 10px;
  bottom: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  font-family: "STKaiti", "KaiTi", "楷体", serif;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.2;
  transform: rotate(-12deg);
  border: 2.5px solid currentColor;
}

/* 内圈：模拟真实圆形印章的双环 */
.seal::before {
  content: '';
  position: absolute;
  inset: 4px;
  border: 1.5px solid currentColor;
  border-radius: 50%;
}

.seal--todo {
  color: #c0392b;
}

.seal--done {
  color: #2e7d32;
}

.accept-btn {
  position: absolute;
  right: 10px;
  bottom: 12px;
  padding: 6px 14px;
  font-size: 16px;
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
  font-size: 14px;
  line-height: 1.5;
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
