<script setup>
import { ref } from 'vue'
import { getLatest } from '@/api'
import { ZONES } from '@/constants'
import PostList from '@/components/PostList.vue'

defineOptions({ name: 'ZonePanel' })

// 36 内容分区（对齐后端 config.py ZONE_NAMES）
const activeZone = ref(21) // 默认资讯

// 分区帖子：后端 /latest 支持 zone 过滤（对齐 routes/main.py）
function zoneFetcher(params) {
  return getLatest({ ...params, zone: activeZone.value })
}
</script>

<template>
  <div class="zone-panel">
    <div class="zone-bar">
      <span
        v-for="z in ZONES"
        :key="z.id"
        class="zone-chip pressable"
        :class="{ 'is-active': z.id === activeZone }"
        @click="activeZone = z.id"
      >{{ z.name }}</span>
    </div>

    <PostList
      :key="activeZone"
      :fetcher="zoneFetcher"
      :cache-key="`list:zone:${activeZone}`"
    />
  </div>
</template>

<style scoped>
.zone-panel {
  background: var(--color-bg);
}

.zone-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px var(--page-margin);
}

.zone-chip {
  flex-shrink: 0;
  padding: 5px 16px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
  background: var(--color-card);
  border: 1px solid var(--color-divider);
  border-radius: 16px;
}

.zone-chip.is-active {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}
</style>
