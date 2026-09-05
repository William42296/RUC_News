<script setup>
import { ref } from 'vue'
import { getLatest } from '@/api'
import { CATEGORY_NAMES } from '@/constants'
import PostList from '@/components/PostList.vue'

defineOptions({ name: 'ZonePanel' })

// 分区 id 1-4（对齐后端 config.py CATEGORY_NAMES）
const zones = Object.entries(CATEGORY_NAMES).map(([id, name]) => ({ id: Number(id), name }))
const activeZone = ref(1)

// 分区帖子：后端 /latest 支持 category 过滤（对齐 routes/main.py）
function zoneFetcher(params) {
  return getLatest({ ...params, category: activeZone.value })
}
</script>

<template>
  <div class="zone-panel">
    <div class="zone-bar">
      <span
        v-for="z in zones"
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
  gap: 8px;
  padding: 10px var(--page-margin);
  overflow-x: auto;
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
