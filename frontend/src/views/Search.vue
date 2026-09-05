<script setup>
import { computed, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { debounce } from 'lodash-es'
import { search as searchApi } from '@/api'
import { getCache, setCache } from '@/utils/cache'
import { getStorage, setStorage, removeStorage } from '@/utils/storage'
import { extractList, extractHasMore } from '@/utils/extract'
import { normalizePost } from '@/utils/normalize'
import { CACHE_KEYS, SEARCH_HISTORY_MAX, ACTION_TYPE } from '@/constants'
import { trackPost } from '@/utils/tracker'
import PostCard from '@/components/PostCard.vue'

// keep-alive 依赖组件名缓存
defineOptions({ name: 'Search' })

const router = useRouter()

const keyword = ref('')          // 输入框当前值
const submittedKeyword = ref('') // 实际已提交搜索的词
const items = ref([])
const page = ref(1)
const loading = ref(false)
const finished = ref(false)
const loaded = ref(false)
const error = ref(false)
const searchTimeMs = ref(null)

const history = ref(getStorage(CACHE_KEYS.SEARCH_HISTORY, []))

const hasResult = computed(() => submittedKeyword.value !== '')

function cacheKeyFor(kw, p) {
  return `${CACHE_KEYS.SEARCH_RES}:${kw}:${p}`
}

function clearResults() {
  submittedKeyword.value = ''
  items.value = []
  page.value = 1
  loaded.value = false
  finished.value = false
  error.value = false
  searchTimeMs.value = null
}

async function fetchPage(kw, p) {
  const res = await searchApi(kw, p)
  const list = extractList(res).map(normalizePost).filter(Boolean)
  const hasMore = extractHasMore(res, list)
  // 搜索耗时：优先取 data.search_time_ms，其次取 res.search_time_ms
  const cost = res?.data?.search_time_ms ?? res?.search_time_ms
  if (cost != null) searchTimeMs.value = cost
  return { list, hasMore }
}

async function runSearch(val) {
  const kw = String(val ?? '').trim()
  if (!kw) return
  submittedKeyword.value = kw
  page.value = 1
  loaded.value = false
  finished.value = false
  error.value = false

  // 缓存优先
  const cached = getCache(cacheKeyFor(kw, 1))
  if (cached) {
    items.value = cached.items || []
    finished.value = cached.finished ?? false
    loaded.value = true
    saveHistory(kw)
    return
  }

  try {
    const { list, hasMore } = await fetchPage(kw, 1)
    items.value = list
    finished.value = !hasMore
    loaded.value = true
    setCache(cacheKeyFor(kw, 1), { items: list, finished: !hasMore })
    saveHistory(kw)
  } catch (e) {
    error.value = true
  }
}

async function loadMore() {
  if (loading.value || finished.value || !submittedKeyword.value) return
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
    clearResults()
    return
  }
  debouncedSearch(val)
}

// 回车 / 搜索键
function onSearchSubmit(val) {
  debouncedSearch.cancel()
  runSearch(val)
}

function onHistoryClick(item) {
  keyword.value = item
  debouncedSearch.cancel()
  runSearch(item)
}

function onItemClick(item) {
  if (!item.id) return
  trackPost(item.id, ACTION_TYPE.CLICK)
  router.push(`/post/${item.id}`)
}

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
    </div>

    <!-- 无搜索词：展示历史 -->
    <div v-if="!hasResult" class="history">
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
      <van-empty v-else description="暂无搜索历史" />
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

        <van-list
          v-model:loading="loading"
          :finished="finished"
          :immediate-check="false"
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
  background: var(--color-card);
}

.history {
  padding: 12px var(--page-margin);
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
