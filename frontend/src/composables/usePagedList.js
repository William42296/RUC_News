import { ref, onMounted } from 'vue'
import { getCache, setCache } from '@/utils/cache'
import { CACHE_TTL } from '@/constants'
import { extractList, extractHasMore } from '@/utils/extract'

/**
 * 通用分页列表逻辑（对应设计文档 5.1 交互与缓存策略）
 * - 缓存优先：有有效缓存先渲染，5 分钟过期后请求并更新
 * - 下拉刷新：重置分页、请求第一页并更新缓存
 * - 上拉加载：page 递增追加
 *
 * 后端响应结构默认假定为 { code, message, data }，
 * data 可为数组或 { list / items / results }，防御性兼容见 utils/extract.js。
 */
export function usePagedList(options) {
  const {
    fetcher,                     // (params) => Promise<res>
    cacheKey = '',               // 缓存键（空则不缓存）
    ttl = CACHE_TTL.LIST,        // 缓存有效期
    pageSize = 10,               // 每页条数（仅作兜底判断）
    normalize = (item) => item,  // 数据项归一化函数
    onData,                       // 可选：每次拿到原始响应时回调（如读取 unread_count）
    paginated = true              // 后端非分页接口（如 /events）置 false，加载完即 finished
  } = options

  const items = ref([])
  const page = ref(1)
  const loading = ref(false)     // 上拉加载中
  const refreshing = ref(false)  // 下拉刷新中
  const finished = ref(false)
  const loaded = ref(false)      // 是否已有数据（控制骨架屏）
  const error = ref(false)

  async function fetchPage(p) {
    // 后端分页参数为 page / limit（见 routes/*.py）
    const res = await fetcher({ page: p, limit: pageSize })
    if (onData) onData(res)
    const list = extractList(res).map(normalize).filter(Boolean)
    const hasMore = extractHasMore(res, list, pageSize)
    return { list, hasMore }
  }

  async function applyFirst() {
    error.value = false
    try {
      const { list, hasMore } = await fetchPage(1)
      items.value = list
      page.value = 1
      finished.value = paginated ? !hasMore : true
      loaded.value = true
      if (cacheKey) {
        setCache(cacheKey, { items: list, page: 1, finished: paginated ? !hasMore : true }, ttl)
      }
    } catch (e) {
      error.value = true
    }
  }

  async function loadFirst() {
    if (cacheKey) {
      const cached = getCache(cacheKey)
      if (cached) {
        items.value = cached.items || []
        page.value = cached.page || 1
        finished.value = cached.finished ?? false
        loaded.value = true
        return
      }
    }
    await applyFirst()
  }

  async function refresh() {
    refreshing.value = true
    await applyFirst()
    refreshing.value = false
  }

  async function loadMore() {
    if (loading.value || refreshing.value || finished.value || !paginated) return
    loading.value = true
    try {
      const next = page.value + 1
      const { list, hasMore } = await fetchPage(next)
      items.value = items.value.concat(list)
      page.value = next
      finished.value = !hasMore
    } catch (e) {
      // 加载更多失败：静默，保留现有数据，允许滚动重试
    } finally {
      loading.value = false
    }
  }

  onMounted(loadFirst)

  return {
    items,
    page,
    loading,
    refreshing,
    finished,
    loaded,
    error,
    loadFirst,
    refresh,
    loadMore
  }
}
