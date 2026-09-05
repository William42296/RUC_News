<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { BOUNTY_TYPES, BOUNTY_STATUS } from '@/constants'
import BountyList from '@/components/BountyList.vue'

defineOptions({ name: 'BountyPanel' })

const router = useRouter()

const activeType = ref('lost')
const activeStatus = ref('unfinished')
const keyword = ref('')

function onSearch(val) {
  const kw = String(val ?? '').trim()
  if (!kw) return
  router.push({ path: '/search', query: { q: kw } })
}
</script>

<template>
  <div class="bounty-panel">
    <!-- 顶部小搜索栏 -->
    <van-search
      v-model="keyword"
      placeholder="搜索悬赏任务"
      shape="round"
      background="transparent"
      @search="onSearch"
    />

    <!-- 一级分类导航：[组队] | [事务招领] | [二手交易] -->
    <div class="bounty-types">
      <span
        v-for="t in BOUNTY_TYPES"
        :key="t.key"
        class="bounty-type pressable"
        :class="{ 'is-active': t.key === activeType }"
        @click="activeType = t.key"
      >{{ t.label }}</span>
    </div>

    <!-- 二级状态筛选：[未完成] | [已完成] -->
    <div class="bounty-status">
      <span
        v-for="s in BOUNTY_STATUS"
        :key="s.key"
        class="status-chip pressable"
        :class="{ 'is-active': s.key === activeStatus }"
        @click="activeStatus = s.key"
      >{{ s.label }}</span>
    </div>

    <BountyList :key="`${activeType}-${activeStatus}`" :type="activeType" :status="activeStatus" />
  </div>
</template>

<style scoped>
.bounty-panel {
  background: var(--color-bg);
}

.bounty-panel :deep(.van-search) {
  padding: 8px var(--page-margin);
}

.bounty-types {
  display: flex;
  gap: 6px;
  padding: 0 var(--page-margin);
}

.bounty-type {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  background: var(--color-card);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
}

.bounty-type.is-active {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
  font-weight: var(--font-weight-card-title);
}

.bounty-status {
  display: flex;
  gap: 10px;
  padding: 10px var(--page-margin) 4px;
}

.status-chip {
  padding: 4px 16px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
  background: var(--color-card);
  border: 1px solid var(--color-divider);
  border-radius: 16px;
}

.status-chip.is-active {
  color: var(--color-primary);
  border-color: var(--color-primary);
  background: rgba(165, 42, 42, 0.06);
}
</style>
