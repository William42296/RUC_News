<template>
  <div ref="sentinel" class="infinite-sentinel">
    <div v-if="loading" class="infinite-sentinel__hint">{{ loadingText }}</div>
    <div v-else-if="finished" class="infinite-sentinel__hint">{{ finishedText }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

/**
 * 无限滚动哨兵：底部不可见元素 + IntersectionObserver。
 * 替换 van-list 的同等位替代品（API 兼容 loading/finished/@load）。
 * - 预加载：rootMargin 底部提前 preload px 触发请求
 * - 内容不足一屏时，加载完成后重新观察以自动补满
 */
const props = defineProps({
  loading: { type: Boolean, default: false },
  finished: { type: Boolean, default: false },
  preload: { type: Number, default: 300 },
  finishedText: { type: String, default: '没有更多了' },
  loadingText: { type: String, default: '加载中...' }
})

const emit = defineEmits(['load'])

const sentinel = ref(null)
let observer = null

function shouldLoad() {
  return !props.loading && !props.finished
}

function onIntersect(entries) {
  if (entries.some((e) => e.isIntersecting) && shouldLoad()) {
    emit('load')
  }
}

onMounted(() => {
  if (!('IntersectionObserver' in window)) return // 极老环境降级：不自动加载
  observer = new IntersectionObserver(onIntersect, {
    rootMargin: `0px 0px ${props.preload}px 0px`
  })
  if (sentinel.value) observer.observe(sentinel.value)
})

// 加载结束后：若哨兵仍在（内容不足一屏），unobserve→observe 强制重算并续载
watch(
  () => props.loading,
  (loading) => {
    if (!loading && observer && sentinel.value && shouldLoad()) {
      observer.unobserve(sentinel.value)
      observer.observe(sentinel.value)
    }
  }
)

onBeforeUnmount(() => {
  if (observer) observer.disconnect()
})
</script>

<style scoped>
.infinite-sentinel {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.infinite-sentinel__hint {
  padding: 16px 0 24px;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: var(--font-size-aux);
}
</style>
