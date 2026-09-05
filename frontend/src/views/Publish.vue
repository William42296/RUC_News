<script setup>
import { reactive, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { debounce } from 'lodash-es'
import { publish } from '@/api'
import { getStorage, setStorage, removeStorage } from '@/utils/storage'
import { CACHE_KEYS, POST_LIMIT } from '@/constants'

defineOptions({ name: 'Publish' })

const router = useRouter()

// 后端 /publish 仅接受 title + content（分区/悬赏类型由后端按特征词自动归类）
const form = reactive({
  title: '',
  content: ''
})

const submitting = ref(false)

// —— 草稿：localStorage 持久化，500ms 防抖自动保存 ——
const draftKey = CACHE_KEYS.DRAFT

function hasContent() {
  return !!(form.title || form.content)
}

function saveDraft() {
  if (!hasContent()) return
  setStorage(draftKey, { ...form })
}

const debouncedSave = debounce(saveDraft, 500)

watch(form, () => debouncedSave(), { deep: true })

onMounted(async () => {
  const draft = getStorage(draftKey)
  if (draft && (draft.title || draft.content)) {
    try {
      await showConfirmDialog({
        title: '草稿',
        message: '检测到未发布的草稿，是否恢复？'
      })
      Object.assign(form, draft)
      showToast('已恢复草稿')
    } catch {
      removeStorage(draftKey)
    }
  }
})

onBeforeUnmount(() => debouncedSave.cancel())

// —— 发布提交 ——
async function onSubmit() {
  const title = form.title.trim()
  const content = form.content.trim()

  if (!title) return showToast('请输入标题')
  if (!content) return showToast('请输入内容')

  debouncedSave.cancel()
  submitting.value = true

  try {
    const res = await publish({ title, content })

    removeStorage(draftKey)
    showToast('发布成功')

    const id = res?.data?.post_id
    router.replace(id ? `/post/${id}` : '/')
  } catch (e) {
    // 发布失败：保留草稿，便于重试（拦截器已 toast 具体原因）
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="page publish">
    <van-nav-bar
      title="发布"
      left-arrow
      fixed
      placeholder
      @click-left="router.back()"
    >
      <template #right>
        <van-button
          type="primary"
          size="small"
          round
          :loading="submitting"
          loading-text="发布中"
          @click="onSubmit"
        >
          发布
        </van-button>
      </template>
    </van-nav-bar>

    <van-form @submit="onSubmit">
      <!-- 标题 -->
      <van-field
        v-model="form.title"
        label="标题"
        type="text"
        :maxlength="POST_LIMIT.TITLE"
        show-word-limit
        placeholder="请输入标题"
      />

      <!-- 内容 -->
      <van-field
        v-model="form.content"
        label="内容"
        type="textarea"
        autosize
        :maxlength="POST_LIMIT.CONTENT"
        show-word-limit
        placeholder="请输入内容"
        rows="6"
      />
    </van-form>
  </div>
</template>

<style scoped>
.publish {
  background: var(--color-page-bg);
}

.publish :deep(.van-cell) {
  background: var(--color-card);
}
</style>
