<script setup>
import { computed, ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { login, getMyPosts, getMyReplies, getMyLikes, getMyCoins } from '@/api'
import { useUserStore } from '@/stores/user'
import { clearCache } from '@/utils/cache'
import { extractList } from '@/utils/extract'
import { normalizePost } from '@/utils/normalize'
import { fromNow } from '@/utils/format'
import PostCard from '@/components/PostCard.vue'

defineOptions({ name: 'My' })

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loggingIn = ref(false)

const isLoggedIn = computed(() => userStore.isLoggedIn)
const nickname = computed(() => userStore.nickname || '未登录用户')
const avatar = computed(() => userStore.avatar)
const avatarText = computed(() => (nickname.value ? nickname.value.slice(0, 1) : '我'))

// —— 代币余额 ——
const coins = ref(0)

// —— 我发 / 我回 / 我赞 ——
const sections = [
  { key: 'posts', label: '我发' },
  { key: 'replies', label: '我回' },
  { key: 'likes', label: '我赞' }
]
const section = ref('')
const items = ref([])
const page = ref(1)
const loading = ref(false)
const finished = ref(false)
const loaded = ref(false)
const error = ref(false)

// —— 登录：POST /my/login（后端校验 crawler session，无需 body）——
async function doLogin() {
  if (loggingIn.value) return
  loggingIn.value = true
  try {
    const res = await login()
    const data = res?.data ?? {}
    if (data.token) userStore.setToken(data.token)
    if (data.nickname) userStore.setUserInfo({ nickname: data.nickname, user_id: data.user_id })
    showToast('登录成功')
    loadCoins()

    const redirect = route.query.redirect
    if (redirect) router.replace(redirect)
  } catch (e) {
    // 拦截器已 toast（Session 无效等）
  } finally {
    loggingIn.value = false
  }
}

async function loadCoins() {
  try {
    const res = await getMyCoins({ page: 1, limit: 1 })
    coins.value = Number(res?.data?.balance ?? 0)
  } catch (e) {
    // 静默
  }
}

// —— 三个列表的加载 ——
async function fetchSection(p) {
  if (section.value === 'posts') return getMyPosts({ page: p, limit: 10 })
  if (section.value === 'replies') return getMyReplies({ page: p, limit: 10 })
  return getMyLikes({ page: p, limit: 10 })
}

function normalizeItem(raw) {
  if (section.value === 'replies') {
    return {
      id: raw.id,
      content: raw.content || '',
      postId: raw.post_id,
      postTitle: raw.post_title || '',
      time: raw.created_at
    }
  }
  return normalizePost(raw)
}

async function applyFirst() {
  error.value = false
  try {
    const res = await fetchSection(1)
    items.value = extractList(res).map(normalizeItem).filter(Boolean)
    page.value = 1
    finished.value = !(res?.data?.has_more ?? false)
    loaded.value = true
  } catch (e) {
    error.value = true
  }
}

async function loadMore() {
  if (loading.value || finished.value) return
  loading.value = true
  const next = page.value + 1
  try {
    const res = await fetchSection(next)
    items.value = items.value.concat(extractList(res).map(normalizeItem).filter(Boolean))
    page.value = next
    finished.value = !(res?.data?.has_more ?? false)
  } catch (e) {
    // 静默
  } finally {
    loading.value = false
  }
}

function openSection(key) {
  section.value = key
  items.value = []
  page.value = 1
  loaded.value = false
  finished.value = false
  applyFirst()
}

function onPostClick(item) {
  const id = item?.postId ?? item?.id
  if (id) router.push(`/post/${id}`)
}

// 登录态变化时刷新余额
onMounted(() => {
  if (isLoggedIn.value) loadCoins()
})

// —— 退出登录（JWT 无服务端状态，客户端清除即可）——
function doLogout() {
  userStore.clearUser()
  section.value = ''
  items.value = []
  coins.value = 0
  showToast('已退出登录')
}

// —— 清除缓存 ——
async function doClearCache() {
  try {
    await showConfirmDialog({ title: '提示', message: '确定清除本地缓存吗？（不影响登录状态）' })
  } catch {
    return
  }
  clearCache()
  showToast('缓存已清除')
}
</script>

<template>
  <div class="page my">
    <van-nav-bar title="我的" fixed placeholder />

    <!-- 用户信息卡片 -->
    <div class="user-card">
      <div class="user-card__avatar">
        <van-image v-if="avatar" round lazy-load :src="avatar" fit="cover" />
        <span v-else class="user-card__avatar-fallback">{{ avatarText }}</span>
      </div>
      <div class="user-card__info">
        <div class="user-card__name">{{ nickname }}</div>
        <div class="user-card__status">
          <template v-if="isLoggedIn">代币余额：{{ coins }}</template>
          <template v-else>点击下方按钮登录</template>
        </div>
      </div>
    </div>

    <!-- 未登录：登录区 -->
    <div v-if="!isLoggedIn" class="login-panel">
      <van-button block round type="primary" :loading="loggingIn" @click="doLogin">
        一键登录
      </van-button>
    </div>

    <!-- 已登录：我发/我回/我赞 + 代币 -->
    <template v-else>
      <!-- 三入口 -->
      <div class="my-sections">
        <span
          v-for="s in sections"
          :key="s.key"
          class="section-tab pressable"
          :class="{ 'is-active': section === s.key }"
          @click="openSection(s.key)"
        >{{ s.label }}</span>
      </div>

      <!-- 列表 -->
      <div v-if="section" class="my-list">
        <div v-if="!loaded && !error" class="skeleton-card">
          <van-skeleton title :row="2" />
        </div>
        <van-empty v-else-if="error && !items.length" description="加载失败，请重试">
          <van-button size="small" type="primary" round @click="applyFirst">重新加载</van-button>
        </van-empty>
        <van-empty v-else-if="loaded && !items.length" description="暂无内容" />
        <template v-else>
          <div
            v-for="item in items"
            :key="item.id"
            class="my-item pressable"
            @click="onPostClick(item)"
          >
            <template v-if="section === 'replies'">
              <div class="reply">
                <div class="reply__content">{{ item.content }}</div>
                <div class="reply__post">回复于：{{ item.postTitle }}</div>
                <div class="reply__time">{{ fromNow(item.time) }}</div>
              </div>
            </template>
            <PostCard v-else :post="item" />
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
      </div>

      <!-- 菜单 -->
      <van-cell-group v-if="!section" inset>
        <van-cell title="清除缓存" is-link icon="delete-o" @click="doClearCache" />
      </van-cell-group>
    </template>

    <!-- 退出登录 -->
    <div v-if="isLoggedIn" class="logout">
      <van-button block round plain type="danger" @click="doLogout">退出登录</van-button>
    </div>
  </div>
</template>

<style scoped>
.my {
  background: var(--color-page-bg);
  padding-bottom: 24px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 12px var(--page-margin);
  padding: 20px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.user-card__avatar {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 50%;
  overflow: hidden;
  background: var(--color-primary);
}

.user-card__avatar :deep(.van-image) {
  width: 100%;
  height: 100%;
}

.user-card__avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 24px;
  color: #fff;
}

.user-card__info {
  flex: 1;
  min-width: 0;
}

.user-card__name {
  font-size: var(--font-size-card-title);
  font-weight: var(--font-weight-card-title);
  color: var(--color-text-primary);
}

.user-card__status {
  margin-top: 4px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.login-panel {
  margin: 0 var(--page-margin);
  padding: 14px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.my-sections {
  display: flex;
  gap: 8px;
  margin: 0 var(--page-margin) 12px;
}

.section-tab {
  flex: 1;
  text-align: center;
  padding: 9px 0;
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  background: var(--color-card);
  border: 1px solid var(--color-divider);
  border-radius: 8px;
}

.section-tab.is-active {
  color: #fff;
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.my-list {
  padding: 0 var(--page-margin);
}

.skeleton-card {
  padding: 14px;
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.my-item {
  margin-bottom: 12px;
}

.reply {
  padding: 12px var(--page-margin);
  background: var(--color-card);
  border-radius: var(--radius-card);
}

.reply__content {
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  word-break: break-word;
}

.reply__post {
  margin-top: 6px;
  font-size: var(--font-size-aux);
  color: var(--color-primary);
}

.reply__time {
  margin-top: 4px;
  font-size: var(--font-size-aux);
  color: var(--color-text-secondary);
}

.logout {
  margin: 24px var(--page-margin);
}
</style>
