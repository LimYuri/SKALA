<template>
  <AuthShell :close-to="loginTarget" close-label="회원가입을 닫고 로그인으로 이동">
    <div class="register-section">
      <h1 class="section-title">회원가입</h1>
      <p class="section-description">기본 정보를 입력하고 Universal StoragE를 시작하세요.</p>

      <form class="register-form" :aria-busy="loading" @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="register-name" class="form-label">이름</label>
          <input
            id="register-name"
            v-model="registerForm.name"
            name="name"
            type="text"
            class="form-input"
            placeholder="홍길동"
            autocomplete="name"
            :disabled="formDisabled"
            required
          />
        </div>

        <div class="form-group">
          <label for="register-email" class="form-label">이메일</label>
          <input
            id="register-email"
            v-model="registerForm.email"
            name="email"
            type="email"
            class="form-input"
            placeholder="user@example.com"
            autocomplete="email"
            inputmode="email"
            :disabled="formDisabled"
            required
          />
        </div>

        <div class="form-group">
          <div class="label-row">
            <label for="register-password" class="form-label">비밀번호</label>
            <span id="password-hint" class="form-hint">8자 이상</span>
          </div>
          <input
            id="register-password"
            v-model="registerForm.password"
            name="password"
            type="password"
            class="form-input"
            placeholder="비밀번호를 입력하세요"
            autocomplete="new-password"
            minlength="8"
            aria-describedby="password-hint"
            :disabled="formDisabled"
            required
          />
        </div>

        <div class="form-group">
          <label for="register-role" class="form-label">역할</label>
          <select
            id="register-role"
            v-model="registerForm.role"
            name="role"
            class="form-input form-select"
            :disabled="formDisabled"
            required
          >
            <option value="STUDENT">구성원(교육생)</option>
            <option value="INSTRUCTOR">자산 운영자(운영진)</option>
          </select>
        </div>

        <div v-if="error" class="form-message error-message" role="alert">
          {{ error }}
        </div>
        <div v-if="success" class="form-message success-message" role="status" aria-live="polite">
          {{ success }}
        </div>

        <button type="submit" class="btn btn-primary submit-button" :disabled="formDisabled">
          <span v-if="loading" class="loading-label">
            <span class="button-spinner" aria-hidden="true"></span>
            가입 중...
          </span>
          <span v-else-if="success">가입 완료</span>
          <span v-else>회원가입</span>
        </button>
      </form>

      <p class="switch-link">
        이미 계정이 있으신가요?
        <router-link :to="loginTarget" class="text-link">로그인으로 돌아가기</router-link>
      </p>
    </div>
  </AuthShell>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AuthShell from '@/components/AuthShell.vue'
import { authApi } from '@/api/auth.js'

const route = useRoute()
const router = useRouter()

const registerForm = ref({
  name: '',
  email: '',
  password: '',
  role: 'STUDENT'
})
const loading = ref(false)
const error = ref('')
const success = ref('')
let redirectTimer

const loginTarget = computed(() => ({
  name: 'Login',
  query: typeof route.query.redirect === 'string'
    ? { redirect: route.query.redirect }
    : {}
}))
const formDisabled = computed(() => loading.value || Boolean(success.value))

async function handleRegister() {
  if (formDisabled.value) return

  error.value = ''
  success.value = ''
  loading.value = true

  try {
    await authApi.register(registerForm.value)
    success.value = '회원가입 완료! 로그인 페이지로 이동합니다.'
    redirectTimer = window.setTimeout(() => {
      router.replace(loginTarget.value)
    }, 1600)
  } catch (e) {
    error.value = e.response?.data?.message || '회원가입에 실패했습니다.'
  } finally {
    loading.value = false
  }
}

onBeforeUnmount(() => {
  if (redirectTimer) window.clearTimeout(redirectTimer)
})
</script>

<style scoped>
.register-section {
  display: flex;
  flex-direction: column;
}

.section-title {
  color: var(--color-navy);
  font-size: clamp(27px, 4vw, 34px);
  line-height: 1.2;
  letter-spacing: -.045em;
}

.section-description {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.register-form {
  margin-top: 23px;
  display: flex;
  flex-direction: column;
  gap: 13px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.form-label {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: 750;
}

.form-hint {
  color: var(--color-text-muted);
  font-size: 11px;
}

.form-input {
  width: 100%;
  height: 45px;
  padding: 0 13px;
  color: var(--color-text-primary);
  background: rgba(255, 255, 255, .74);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: var(--transition);
}

.form-input:hover:not(:disabled) {
  border-color: var(--color-border-hover);
  background: var(--color-bg-primary);
}

.form-input:focus {
  border-color: var(--color-primary);
  background: var(--color-bg-primary);
  box-shadow: 0 0 0 3px var(--color-primary-soft);
}

.form-input:user-invalid {
  border-color: rgba(169, 68, 66, .58);
}

.form-input:disabled {
  cursor: not-allowed;
  color: var(--color-text-muted);
  background: var(--color-bg-tertiary);
  opacity: .75;
}

.form-select {
  cursor: pointer;
}

.form-message {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-size: 12px;
  line-height: 1.55;
}

.error-message {
  color: var(--color-danger);
  background: var(--color-danger-light);
  border: 1px solid rgba(169, 68, 66, .2);
}

.success-message {
  color: var(--color-success);
  background: var(--color-success-light);
  border: 1px solid rgba(37, 99, 235, .2);
}

.submit-button {
  width: 100%;
  min-height: 48px;
  margin-top: 3px;
}

.loading-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.button-spinner {
  width: 15px;
  height: 15px;
  border: 2px solid rgba(255, 255, 255, .42);
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin .72s linear infinite;
}

.switch-link {
  margin-top: 17px;
  color: var(--color-text-secondary);
  font-size: 12px;
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

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 520px) {
  .register-form {
    margin-top: 20px;
  }
}
</style>
