<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { debounce } from 'lodash-es'
import { search as searchApi, getSearchHot } from '@/api'
import { getCache, setCache } from '@/utils/cache'
import { getStorage, setStorage, removeStorage } from '@/utils/storage'
import { extractList, extractHasMore } from '@/utils/extract'
import { normalizePost } from '@/utils/normalize'
import { CACHE_KEYS, SEARCH_HISTORY_MAX, ACTION_TYPE } from '@/constants'
import { trackPost } from '@/utils/tracker'
import PostCard from '@/components/PostCard.vue'
import InfiniteSentinel from '@/components/InfiniteSentinel.vue'

// keep-alive 依赖组件名缓存
defineOptions({ name: 'Search' })

const router = useRouter()
const route = useRoute()

const keyword = ref('')          // 输入框当前值
const submittedKeyword = ref('') // 实际已提交搜索的词
const postTypeFilter = ref('')   // 快捷分类过滤（lost/secondhand/team）
const items = ref([])
const page = ref(1)
const loading = ref(false)
const finished = ref(false)
const loaded = ref(false)
const error = ref(false)
const searchTimeMs = ref(null)

const history = ref(getStorage(CACHE_KEYS.SEARCH_HISTORY, []))

// 快捷分类胶囊（浅蓝底深蓝字）
const QUICK_TYPES = [
  { key: 'secondhand', label: '二手交易' },
  { key: 'lost', label: '失物招领' },
  { key: 'team', label: '组队' }
]

// 大家都在搜
const hotList = ref([])
const hotOffset = ref(0)
const hotHidden = ref(getStorage(CACHE_KEYS.SEARCH_HOT_HIDDEN, false))

const hasResult = computed(() => submittedKeyword.value !== '' || postTypeFilter.value !== '')

function cacheKeyFor(kw, p) {
  return `${CACHE_KEYS.SEARCH_RES}:${kw}:${postTypeFilter.value}:${p}`
}

function clearResults() {
  submittedKeyword.value = ''
  postTypeFilter.value = ''
  items.value = []
  page.value = 1
  loaded.value = false
  finished.value = false
  error.value = false
  searchTimeMs.value = null
}

// 返回初始发现页：清空输入、结果与快捷分类筛选
function resetToDiscover() {
  debouncedSearch.cancel()
  keyword.value = ''
  clearResults()
}

async function fetchPage(kw, p) {
  const res = await searchApi(kw, p, postTypeFilter.value)
  const list = extractList(res).map(normalizePost).filter(Boolean)
  const hasMore = extractHasMore(res, list)
  const cost = res?.data?.search_time_ms ?? res?.search_time_ms
  if (cost != null) searchTimeMs.value = cost
  return { list, hasMore }
}

async function runSearch(val) {
  const kw = String(val ?? '').trim()
  submittedKeyword.value = kw
  page.value = 1
  loaded.value = false
  finished.value = false
  error.value = false

  if (!kw && !postTypeFilter.value) return

  const cached = getCache(cacheKeyFor(kw, 1))
  if (cached) {
    items.value = cached.items || []
    finished.value = cached.finished ?? false
    loaded.value = true
    if (kw) saveHistory(kw)
    return
  }

  try {
    const { list, hasMore } = await fetchPage(kw, 1)
    items.value = list
    finished.value = !hasMore
    loaded.value = true
    setCache(cacheKeyFor(kw, 1), { items: list, finished: !hasMore })
    if (kw) saveHistory(kw)
  } catch (e) {
    error.value = true
  }
}

async function loadMore() {
  if (loading.value || finished.value || !hasResult.value) return
  loading.value = true
  const kw = submittedKeyword.value
  const next = page.value + 1
  try {
    const cached = getCache(cacheKeyFor(kw, next))
    if (cached) {
      items.value = items.value.concat(cached.items || [])
      finished.value = cached.finished ?? false
    } else {
      const { list, hasMore } = await fetchPage(kw, next)
      items.value = items.value.concat(list)
      finished.value = !hasMore
      setCache(cacheKeyFor(kw, next), { items: list, finished: !hasMore })
    }
    page.value = next
  } catch (e) {
    // 加载更多失败：静默，允许重试
  } finally {
    loading.value = false
  }
}

function saveHistory(kw) {
  const next = [kw, ...history.value.filter((h) => h !== kw)].slice(0, SEARCH_HISTORY_MAX)
  history.value = next
  setStorage(CACHE_KEYS.SEARCH_HISTORY, next)
}

function clearHistory() {
  history.value = []
  removeStorage(CACHE_KEYS.SEARCH_HISTORY)
}

// 输入防抖 500ms
const debouncedSearch = debounce((val) => runSearch(val), 500)

function onInput(val) {
  keyword.value = val
  if (!val.trim()) {
    debouncedSearch.cancel()
    if (!postTypeFilter.value) clearResults()
    return
  }
  debouncedSearch(val)
}

function onSearchSubmit(val) {
  debouncedSearch.cancel()
  runSearch(val)
}

function onHistoryClick(item) {
  keyword.value = item
  debouncedSearch.cancel()
  runSearch(item)
}

// 快捷分类点击：触发搜索并按 post_type 过滤
function onQuickType(t) {
  postTypeFilter.value = t.key
  keyword.value = ''
  debouncedSearch.cancel()
  runSearch('')
}

// 大家都在搜
async function loadHot(offset = 0) {
  try {
    const res = await getSearchHot({ offset })
    const raw = res?.data?.hot ?? []
    if (raw.length) {
      hotList.value = raw
      hotOffset.value = offset
    } else if (offset > 0) {
      // 换一换到末尾：回到开头
      await loadHot(0)
    }
  } catch (e) {
    // 静默
  }
}

function onHotClick(item) {
  keyword.value = item.title
  debouncedSearch.cancel()
  runSearch(item.title)
}

function onHotRefresh() {
  loadHot(hotOffset.value + 10)
}

function onHotClose() {
  hotHidden.value = true
  setStorage(CACHE_KEYS.SEARCH_HOT_HIDDEN, true)
}

function onItemClick(item) {
  if (!item.id) return
  trackPost(item.id, ACTION_TYPE.CLICK)
  router.push(`/post/${item.id}`)
}

onMounted(() => {
  if (!hotHidden.value) loadHot(0)
  // 从悬赏/大事件搜索栏跳转而来，携带 ?q= 预填并搜索
  const q = String(route.query.q ?? '').trim()
  if (q) {
    keyword.value = q
    runSearch(q)
  }
})

onBeforeUnmount(() => {
  debouncedSearch.cancel()
})
</script>

<template>
  <div class="page search">
    <!-- 顶部固定搜索框 -->
    <div class="search-bar">
      <van-search
        :model-value="keyword"
        placeholder="搜索资讯 / 帖子"
        clearable
        @update:model-value="onInput"
        @search="onSearchSubmit"
      />
      <span v-if="hasResult" class="search-bar__cancel pressable" @click="resetToDiscover">取消</span>
    </div>

    <!-- 无搜索词：展示历史 + 大家都在搜 + 快捷分类 -->
    <div v-if="!hasResult" class="discover">
      <!-- 大家都在搜 -->
      <div v-if="!hotHidden && hotList.length" class="hot">
        <div class="hot__header">
          <span class="hot__title">大家都在搜</span>
          <div class="hot__actions">
            <span class="hot__action" @click="onHotRefresh">换一换</span>
            <van-icon name="cross" class="hot__action" @click="onHotClose" />
          </div>
        </div>
        <div class="hot__tags">
          <span
            v-for="h in hotList"
            :key="h.id"
            class="hot__tag pressable"
            @click="onHotClick(h)"
          >{{ h.title }}</span>
        </div>
      </div>

      <!-- 快捷分类胶囊：浅蓝底深蓝字 -->
      <div class="quick">
        <div class="quick__header">快捷分类</div>
        <div class="quick__tags">
          <span
            v-for="t in QUICK_TYPES"
            :key="t.key"
            class="quick__capsule pressable"
            @click="onQuickType(t)"
          >{{ t.label }}</span>
        </div>
      </div>

      <!-- 搜索历史 -->
      <div class="history">
        <template v-if="history.length">
          <div class="history__header">
            <span class="history__title">搜索历史</span>
            <van-icon name="delete-o" class="history__clear" @click="clearHistory" />
          </div>
          <div class="history__tags">
            <van-tag
              v-for="h in history"
              :key="h"
              plain
              type="primary"
              size="medium"
              @click="onHistoryClick(h)"
            >
              {{ h }}
            </van-tag>
          </div>
        </template>
      </div>
    </div>

    <!-- 有搜索词：展示结果 -->
    <template v-else>
      <!-- 搜索耗时 -->
      <div v-if="loaded && searchTimeMs != null" class="search-cost">
        搜索耗时 {{ searchTimeMs }} 毫秒
      </div>

      <!-- 骨架屏 -->
      <div v-if="!loaded && !error">
        <div v-for="i in 3" :key="i" class="skeleton-card">
          <van-skeleton title :row="2" />
        </div>
      </div>

      <!-- 失败 -->
      <van-empty v-else-if="error && !items.length" description="搜索失败，请重试" />

      <!-- 空结果 -->
      <van-empty v-else-if="loaded && !items.length" description="未找到相关结果" />

      <!-- 结果列表 -->
      <template v-else>
        <div
          v-for="item in items"
          :key="item.id"
          class="list-item pressable"
          @click="onItemClick(item)"
        >
          <PostCard :post="item" :keyword="submittedKeyword" />
        </div>

        <InfiniteSentinel
          :loading="loading"
          :finished="finished"
          finished-text="—— 没有更多了 ——"
          loading-text="加载中..."
          @load="loadMore"
        />
      </template>
    </template>
  </div>
</template>

<style scoped>
.search-bar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  padding-right: var(--page-margin);
  background: var(--color-card);
}

.search-bar :deep(.van-search) {
  flex: 1;
  padding-right: 0;
}

.search-bar__cancel {
  flex-shrink: 0;
  padding-left: 12px;
  font-size: var(--font-size-body);
  color: var(--color-primary);
}

.discover {
  padding: 12px var(--page-margin);
}

.hot {
  padding: 12px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.hot__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.hot__title {
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.hot__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.hot__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.hot__tag {
  padding: 4px 14px;
  font-size: var(--font-size-aux);
  color: var(--color-text-primary);
  background: var(--color-bg);
  border-radius: 999px;
}

.quick {
  margin-top: 14px;
  padding: 12px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.quick__header {
  margin-bottom: 12px;
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.quick__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.quick__capsule {
  padding: 5px 16px;
  font-size: var(--font-size-aux);
  color: #1d4f8f;                 /* 深蓝字 */
  background: #e3efff;            /* 浅蓝底 */
  border-radius: 999px;
}

.history {
  margin-top: 14px;
}

.history__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.history__title {
  font-size: var(--font-size-body);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.history__clear {
  color: var(--color-text-secondary);
}

.history__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.search-cost {
  padding: 8px var(--page-margin) 0;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.skeleton-card {
  margin: 0 var(--page-margin) 12px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}
</style>
