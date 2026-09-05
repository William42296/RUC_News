<template>
  <article class="post-card">
    <h3 class="post-card__title ellipsis-2">
      <template v-for="(seg, i) in titleSegments" :key="i">
        <span v-if="seg.match" class="highlight">{{ seg.text }}</span>
        <template v-else>{{ seg.text }}</template>
      </template>
    </h3>

    <p v-if="post.summary" class="post-card__summary ellipsis">
      <template v-for="(seg, i) in summarySegments" :key="i">
        <span v-if="seg.match" class="highlight">{{ seg.text }}</span>
        <template v-else>{{ seg.text }}</template>
      </template>
    </p>

    <div class="post-card__meta">
      <span v-if="tagLabel" class="post-card__tag" :style="tagStyle">{{ tagLabel }}</span>
      <span class="post-card__time">{{ fromNow(post.time) }}</span>
      <span class="post-card__comments">
        <van-icon name="comment-o" />
        <span class="post-card__count">{{ post.commentCount }}</span>
      </span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { fromNow } from '@/utils/format'
import { highlightSegments } from '@/utils/highlight'

const props = defineProps({
  post: { type: Object, required: true },
  // 可选：搜索关键词，用于标题/摘要高亮
  keyword: { type: String, default: '' }
})

// 标签配色：按 post_type 映射功能色（lost/secondhand/team/event），其余走主色
const POST_TYPE_STYLES = {
  lost: { color: '#B03A2E', bg: 'rgba(176, 58, 46, 0.12)' },
  secondhand: { color: '#C99335', bg: 'rgba(201, 147, 53, 0.12)' },
  team: { color: '#7C9E55', bg: 'rgba(124, 158, 85, 0.14)' },
  event: { color: '#8E6BB0', bg: 'rgba(142, 107, 176, 0.14)' }
}
const DEFAULT_TAG = { color: '#A52A2A', bg: 'rgba(165, 42, 42, 0.10)' }

const tagLabel = computed(() => props.post.categoryName || props.post.category || '')
const tagStyle = computed(() => POST_TYPE_STYLES[props.post.postType] || DEFAULT_TAG)
const titleSegments = computed(() => highlightSegments(props.post.title, props.keyword))
const summarySegments = computed(() => highlightSegments(props.post.summary, props.keyword))
</script>

<style scoped>
.post-card {
  margin: 0 var(--page-margin) 12px;
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-card);
}

.post-card__title {
  margin: 0;
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-card-title);
  line-height: 1.4;
  color: var(--color-text-primary);
}

.post-card__summary {
  margin: 6px 0 0;
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
}

.post-card__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.post-card__tag {
  padding: 1px 8px;
  border-radius: 999px;
  line-height: 1.6;
  white-space: nowrap;
}

.post-card__time {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-card__comments {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  white-space: nowrap;
}

.post-card__count {
  font-size: var(--font-size-aux);
}
</style>
