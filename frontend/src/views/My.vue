<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { login } from '@/api'
import { useUserStore } from '@/stores/user'
import { clearCache } from '@/utils/cache'

defineOptions({ name: 'My' })

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const loggingIn = ref(false)

const isLoggedIn = computed(() => userStore.isLoggedIn)
const nickname = computed(() => userStore.nickname || '未登录用户')
const avatar = computed(() => userStore.avatar)
const avatarText = computed(() => (nickname.value ? nickname.value.slice(0, 1) : '我'))

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

    // 若由权限守卫跳转而来，登录后回到原目标页
    const redirect = route.query.redirect
    if (redirect) router.replace(redirect)
  } catch (e) {
    // 拦截器已 toast（Session 无效等）
  } finally {
    loggingIn.value = false
  }
}

// —— 退出登录（JWT 无服务端状态，客户端清除即可）——
function doLogout() {
  userStore.clearUser()
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
        <div class="user-card__status">{{ isLoggedIn ? '已登录' : '点击下方按钮登录' }}</div>
      </div>
    </div>

    <!-- 未登录：登录区 -->
    <div v-if="!isLoggedIn" class="login-panel">
      <van-button block round type="primary" :loading="loggingIn" @click="doLogin">
        一键登录
      </van-button>
    </div>

    <!-- 已登录：菜单 -->
    <van-cell-group v-else inset>
      <van-cell title="清除缓存" is-link icon="delete-o" @click="doClearCache" />
    </van-cell-group>

    <!-- 退出登录 -->
    <div v-if="isLoggedIn" class="logout">
      <van-button block round plain type="danger" @click="doLogout">退出登录</van-button>
    </div>
  </div>
</template>

<style scoped>
.my {
  background: var(--color-page-bg);
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

.logout {
  margin: 24px var(--page-margin);
}
</style>
