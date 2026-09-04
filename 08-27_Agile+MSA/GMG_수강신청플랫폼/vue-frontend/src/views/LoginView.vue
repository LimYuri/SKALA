<template>
  <AuthShell close-to="/" close-label="로그인을 닫고 홈으로 이동">
    <div class="login-section">
      <h1 class="section-title">로그인</h1>

      <div v-if="expired" class="session-notice" role="status">
        안전을 위해 로그인 시간이 만료되었습니다. 다시 로그인해 주세요.
      </div>

      <form class="login-form" :aria-busy="loading" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="login-email" class="form-label">이메일</label>
          <input
            id="login-email"
            v-model.trim="credentials.username"
            name="username"
            type="email"
            class="form-input"
            placeholder="user@example.com"
            autocomplete="username"
            :disabled="loading"
            required
          />
        </div>

        <div class="form-group">
          <label for="login-password" class="form-label">비밀번호</label>
          <input
            id="login-password"
            v-model="credentials.password"
            name="password"
            type="password"
            class="form-input"
            placeholder="비밀번호를 입력하세요"
            autocomplete="current-password"
            :disabled="loading"
            required
          />
        </div>

        <div v-if="error" class="form-message error-message" role="alert">
          {{ error }}
        </div>

        <button type="submit" class="btn btn-primary login-button" :disabled="loading">
          <span v-if="loading" class="loading-label">
            <span class="button-spinner" aria-hidden="true"></span>
            로그인 중...
          </span>
          <template v-else>
            로그인
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 12h14M14 7l5 5-5 5" />
            </svg>
          </template>
        </button>
      </form>

      <p class="switch-link">
        계정이 없으신가요?
        <router-link :to="registerTarget" class="text-link">회원가입</router-link>
      </p>
    </div>
  </AuthShell>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import AuthShell from '@/components/AuthShell.vue'
import { useAuthStore } from '@/store/auth.js'

const auth = useAuthStore()
const route = useRoute()
const credentials = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')

const expired = computed(() => route.query.expired === '1')
const registerTarget = computed(() => ({
  name: 'Register',
  query: typeof route.query.redirect === 'string'
    ? { redirect: route.query.redirect }
    : {}
}))

async function handleLogin() {
  if (loading.value) return

  loading.value = true
  error.value = ''

  try {
    await auth.loginWithCredentials(
      credentials.username,
      credentials.password,
      route.query.redirect || '/groups'
    )
  } catch (e) {
    error.value = e.message || '로그인에 실패했습니다.'
    credentials.password = ''
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-section {
  display: flex;
  flex-direction: column;
}

.section-title {
  color: var(--color-navy);
  font-size: clamp(28px, 4vw, 36px);
  line-height: 1.2;
  letter-spacing: -.045em;
}

.section-description {
  margin-top: 11px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.session-notice {
  margin-top: 24px;
  padding: 12px 14px;
  color: var(--color-warning);
  background: var(--color-warning-light);
  border: 1px solid rgba(37, 99, 235, .2);
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.55;
}

.login-form {
  margin-top: 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.form-label {
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 700;
}

.form-input {
  width: 100%;
  min-height: 47px;
  padding: 0 14px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font: inherit;
  transition: var(--transition);
}

.form-input:hover:not(:disabled) {
  border-color: var(--color-primary-light);
}

.form-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(42, 101, 216, .12);
  outline: none;
}

.form-input:disabled {
  cursor: not-allowed;
  opacity: .65;
}

.form-message {
  padding: 11px 13px;
  border-radius: var(--radius-md);
  font-size: 13px;
  line-height: 1.5;
}

.error-message {
  color: var(--color-danger);
  background: var(--color-danger-light);
  border: 1px solid rgba(190, 45, 45, .18);
}

.login-button {
  width: 100%;
  min-height: 50px;
  margin-top: 4px;
  justify-content: space-between;
  padding-inline: 20px;
}

.loading-label {
  display: inline-flex;
  align-items: center;
  gap: 9px;
}

.button-spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, .45);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin .7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.login-button svg {
  width: 19px;
  height: 19px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
  transition: transform .22s ease;
}

.login-button:hover svg {
  transform: translateX(2px);
}

.switch-link {
  margin-top: 20px;
  color: var(--color-text-secondary);
  font-size: 13px;
  text-align: center;
}

.text-link {
  margin-left: 4px;
  color: var(--color-primary);
  font-weight: 750;
  text-decoration: underline;
  text-decoration-color: transparent;
  text-underline-offset: 3px;
  transition: var(--transition);
}

.text-link:hover {
  color: var(--color-primary-dark);
  text-decoration-color: currentColor;
}
</style>
