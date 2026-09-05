<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { getPostDetail, publishComment } from '@/api'
import { getCache, setCache } from '@/utils/cache'
import { normalizePost, normalizeComment } from '@/utils/normalize'
import { CACHE_KEYS, ACTION_TYPE } from '@/constants'
import { fromNow } from '@/utils/format'
import { trackPost } from '@/utils/tracker'

defineOptions({ name: 'PostDetail' })

const route = useRoute()
const router = useRouter()
const postId = route.params.id

// 上报帖子浏览（推荐矩阵更新）
trackPost(Number(postId), ACTION_TYPE.VIEW)

const cacheKey = `${CACHE_KEYS.POST_DETAIL}:${postId}`

const post = ref(null)
const comments = ref([])
const commentCount = ref(0)
const loaded = ref(false)
const error = ref(false)

const commentText = ref('')
const sending = ref(false)

// —— 详情响应解析：后端返回扁平帖子对象（含 comments_count，无评论列表）——
function parseDetail(res) {
  const data = res?.data
  const rawPost = data?.post ?? data ?? null
  // 后端暂无「评论列表」接口，历史评论无法拉取；仅本会话新发评论上屏
  const rawComments = data?.comments ?? data?.comment_list ?? rawPost?.comments ?? []
  return {
    post: normalizePost(rawPost),
    comments: (Array.isArray(rawComments) ? rawComments : []).map(normalizeComment).filter(Boolean)
  }
}

function apply(payload) {
  post.value = payload.post
  comments.value = payload.comments || []
  commentCount.value =
    Number(payload.post?.commentCount) || 0 || comments.value.length
  loaded.value = true
}

async function loadDetail() {
  const cached = getCache(cacheKey)
  if (cached) {
    apply(cached)
    return
  }
  try {
    const res = await getPostDetail(postId)
    const payload = parseDetail(res)
    setCache(cacheKey, payload)
    apply(payload)
  } catch (e) {
    error.value = true
  }
}
loadDetail()

// —— 正文链接识别：按 URL 切分为文本/链接片段，避免 v-html 注入 ——
const URL_RE = /(https?:\/\/[^\s<>"'()]+)/g
const contentSegments = computed(() => {
  const text = post.value?.content || ''
  const segs = []
  let last = 0
  let m
  URL_RE.lastIndex = 0
  while ((m = URL_RE.exec(text))) {
    if (m.index > last) segs.push({ type: 'text', value: text.slice(last, m.index) })
    segs.push({ type: 'link', value: m[0] })
    last = m.index + m[0].length
  }
  if (last < text.length) segs.push({ type: 'text', value: text.slice(last) })
  return segs
})

// —— 发布评论（乐观更新 + 失败回滚）——
async function onSendComment() {
  const content = commentText.value.trim()
  if (!content) return showToast('请输入评论内容')
  if (sending.value) return

  const tempId = `local_${Date.now()}`
  const temp = { id: tempId, content, author: '我', time: Date.now(), pending: true }

  // 乐观更新：立即上屏
  comments.value = comments.value.concat([temp])
  commentCount.value += 1
  commentText.value = ''
  sending.value = true

  try {
    // 字段名以后端 config.py 为准，集中在此调整
    const res = await publishComment({ post_id: postId, content })
    const saved = normalizeComment(res?.data?.comment ?? res?.data ?? null)
    comments.value = comments.value.map((c) => {
      if (c.id !== tempId) return c
      return saved && saved.id ? { ...saved, pending: false } : { ...c, pending: false }
    })
  } catch (e) {
    // 失败回滚
    comments.value = comments.value.filter((c) => c.id !== tempId)
    commentCount.value -= 1
    showToast('评论失败，请重试')
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div class="page detail">
    <van-nav-bar title="帖子详情" left-arrow fixed placeholder @click-left="router.back()" />

    <!-- 骨架屏 -->
    <div v-if="!loaded && !error" class="detail__body">
      <van-skeleton title :row="6" />
    </div>

    <!-- 加载失败 -->
    <van-empty v-else-if="error" description="加载失败，请重试">
      <van-button size="small" type="primary" round @click="loadDetail">重新加载</van-button>
    </van-empty>

    <!-- 正文 -->
    <template v-else>
      <article class="detail__body">
        <h1 class="detail__title">{{ post.title }}</h1>

        <div class="detail__meta">
          <span v-if="post.category" class="detail__tag">{{ post.category }}</span>
          <span class="detail__time">{{ fromNow(post.time) }}</span>
        </div>

        <p class="detail__content">
          <template v-for="(seg, i) in contentSegments" :key="i">
            <a
              v-if="seg.type === 'link'"
              :href="seg.value"
              target="_blank"
              rel="noopener noreferrer"
              class="detail__link"
            >{{ seg.value }}</a>
            <template v-else>{{ seg.value }}</template>
          </template>
        </p>
      </article>

      <van-divider>评论 {{ commentCount }}</van-divider>

      <!-- 评论列表 -->
      <div class="comment-list">
        <van-empty v-if="!comments.length" description="暂无评论，快来抢沙发" />
        <div v-for="c in comments" :key="c.id" class="comment">
          <div class="comment__head">
            <span class="comment__author">{{ c.author || '匿名' }}</span>
            <span class="comment__time">
              {{ c.pending ? '发送中…' : fromNow(c.time) }}
            </span>
          </div>
          <p class="comment__content">{{ c.content }}</p>
        </div>
      </div>
    </template>

    <!-- 底部评论输入栏 -->
    <div class="comment-bar">
      <van-field
        v-model="commentText"
        type="text"
        placeholder="说点什么…"
        border
        @keyup.enter="onSendComment"
      >
        <template #button>
          <van-button
            type="primary"
            size="small"
            :loading="sending"
            @click="onSendComment"
          >
            发送
          </van-button>
        </template>
      </van-field>
    </div>
  </div>
</template>

<style scoped>
.detail {
  padding-bottom: 68px;
  background: var(--color-page-bg);
}

.detail__body {
  padding: 16px var(--page-margin);
  background: var(--color-card);
}

.detail__title {
  margin: 0;
  font-size: var(--font-size-title);
  font-weight: var(--font-weight-card-title);
  line-height: 1.4;
  color: var(--color-text-primary);
}

.detail__meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.detail__tag {
  padding: 1px 8px;
  border-radius: 999px;
  color: #4a90d9;
  background: rgba(74, 144, 217, 0.12);
  line-height: 1.6;
}

.detail__content {
  margin: 14px 0 0;
  font-size: var(--font-size-body);
  line-height: 1.7;
  color: var(--color-text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.detail__link {
  color: var(--color-primary);
  word-break: break-all;
}

.comment-list {
  padding: 0 var(--page-margin);
}

.comment {
  margin-bottom: 14px;
  padding: 12px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.comment__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--font-size-aux);
}

.comment__author {
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.comment__time {
  color: var(--color-text-secondary);
}

.comment__content {
  margin: 6px 0 0;
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  word-break: break-word;
}

.comment-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 8px var(--page-margin) calc(8px + env(safe-area-inset-bottom));
  background: var(--color-card);
  box-shadow: 0 -1px 8px rgba(0, 0, 0, 0.04);
}
</style>
