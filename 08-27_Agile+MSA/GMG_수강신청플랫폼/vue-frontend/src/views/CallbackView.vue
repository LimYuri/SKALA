<template>
  <div class="callback-page">
    <div class="callback-brand"><GearHubLogo /></div>
    <div class="callback-box surface" role="status" aria-live="polite">
      <div class="spinner"></div>
      <p>{{ message }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import GearHubLogo from '@/components/GearHubLogo.vue'
import { useAuthStore } from '@/store/auth.js'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const message = ref('로그인 처리 중...')
const processing = ref(false)

onMounted(async () => {
  if (processing.value) return
  processing.value = true

  const code = route.query.code
  const error = route.query.error
  const errorDescription = route.query.error_description

  if (error) {
    console.error('OAuth callback error:', {
      error,
      errorDescription
    })
    message.value = '로그인에 실패했습니다. 다시 시도해주세요.'
    router.replace('/login')
    return
  }

  if (!code) {
    console.error('OAuth callback error: code 파라미터가 없습니다.')
    message.value = '잘못된 로그인 요청입니다.'
    router.replace('/login')
    return
  }

  try {
    await auth.handleCallback(code)
    message.value = '로그인 완료! 이동 중입니다...'
    router.replace(auth.consumePostLoginRedirect())
  } catch (err) {
    console.error('OAuth callback 처리 실패:', err)
    message.value = '로그인 처리에 실패했습니다.'
    router.replace('/login')
  }
})
</script>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 18px;
  padding: 24px;
  background: linear-gradient(135deg, #edf5ff, #f8fbff);
}

.callback-box {
  width: min(100%, 420px);
  min-height: 180px;
  padding: 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: var(--color-text-secondary);
  font-size: 15px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
