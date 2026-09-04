import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth.js'

const AUTH_SERVER_URL = import.meta.env.VITE_AUTH_SERVER_URL || '/auth'
const POST_LOGIN_REDIRECT_KEY = 'post_login_redirect'

function readStoredUser() {
  try {
    return JSON.parse(sessionStorage.getItem('user') || 'null')
  } catch {
    sessionStorage.removeItem('user')
    return null
  }
}

function decodeTokenPayload(token) {
  try {
    const encoded = token.split('.')[1]
    if (!encoded) return null
    const normalized = encoded.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
    return JSON.parse(decodeURIComponent(escape(atob(padded))))
  } catch {
    return null
  }
}

function readStoredToken() {
  const token = sessionStorage.getItem('access_token')
  if (!token) return null

  const payload = decodeTokenPayload(token)
  if (payload?.exp && payload.exp * 1000 <= Date.now()) {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('user')
    return null
  }
  return token
}

export const useAuthStore = defineStore('auth', () => {
  const initialToken = readStoredToken()
  const accessToken = ref(initialToken)
  const user = ref(initialToken ? readStoredUser() : null)

  const isAuthenticated = computed(() => !!accessToken.value)
  const isInstructor = computed(() => user.value?.role === 'INSTRUCTOR')

  function setToken(token) {
    accessToken.value = token
    sessionStorage.setItem('access_token', token)
  }

  function setUser(userData) {
    user.value = userData
    sessionStorage.setItem('user', JSON.stringify(userData))
  }

  async function fetchUser() {
    try {
      const res = await authApi.getMe()

      const userData = res?.data?.data ?? res?.data

      if (!userData || typeof userData !== 'object') {
        throw new Error('사용자 정보 형식이 올바르지 않습니다.')
      }

      setUser(userData)
    } catch (error) {
      console.error('[AuthStore] 사용자 정보 조회 실패:', error)
      logout(false)
    }
  }

  function clearSession() {
    accessToken.value = null
    user.value = null
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('user')
    sessionStorage.removeItem('current_group_id')
  }

  async function logout(redirect = true, revokeSso = false) {
    clearSession()

    if (revokeSso) {
      try {
        await fetch(`${AUTH_SERVER_URL}/logout`, {
          method: 'GET',
          credentials: 'include',
          mode: 'no-cors',
          cache: 'no-store',
          keepalive: true
        })
      } catch {
        // 로컬 세션은 이미 제거했으므로 인증 서버 로그아웃 실패가 화면을 막지 않게 한다.
      }
    }

    if (redirect) {
      window.location.assign('/login')
    }
  }

  // OAuth2 Authorization Code Flow
  function createAuthorizationUrl(redirectPath = '/groups') {
    const safeRedirect = typeof redirectPath === 'string' && redirectPath.startsWith('/')
      ? redirectPath
      : '/groups'
    sessionStorage.setItem(POST_LOGIN_REDIRECT_KEY, safeRedirect)

    const params = new URLSearchParams({
      response_type: 'code',
      client_id: import.meta.env.VITE_CLIENT_ID,
      redirect_uri: import.meta.env.VITE_REDIRECT_URI,
      scope: 'openid profile read write'
    })

    return `${AUTH_SERVER_URL}/oauth2/authorize?${params.toString()}`
  }

  function redirectToLogin(redirectPath = '/groups') {
    window.location.href = createAuthorizationUrl(redirectPath)
  }

  async function loginWithCredentials(username, password, redirectPath = '/groups') {
    const authorizationUrl = createAuthorizationUrl(redirectPath)

    // Authorization 요청으로 서버 세션과 SavedRequest를 먼저 만든다.
    await fetch(authorizationUrl, {
      credentials: 'include',
      cache: 'no-store'
    })

    const response = await fetch(`${AUTH_SERVER_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: new URLSearchParams({ username, password }),
      credentials: 'include',
      cache: 'no-store'
    })

    const finalUrl = new URL(response.url, window.location.origin)
    if (finalUrl.pathname === '/auth/login' && finalUrl.searchParams.has('error')) {
      throw new Error('이메일 또는 비밀번호가 올바르지 않습니다.')
    }

    if (finalUrl.pathname !== '/callback' || !finalUrl.searchParams.has('code')) {
      throw new Error('인증 서버의 로그인 응답을 확인할 수 없습니다.')
    }

    window.location.assign(`${finalUrl.pathname}${finalUrl.search}`)
  }

  function consumePostLoginRedirect() {
    const redirectPath = sessionStorage.getItem(POST_LOGIN_REDIRECT_KEY) || '/groups'
    sessionStorage.removeItem(POST_LOGIN_REDIRECT_KEY)
    return redirectPath.startsWith('/') ? redirectPath : '/groups'
  }

  async function handleCallback(code) {
    const res = await authApi.exchangeCode(code)

    const token = res?.data?.access_token

    if (!token) {
      throw new Error('액세스 토큰을 받지 못했습니다.')
    }

    setToken(token)
    await fetchUser()
  }

  return {
    accessToken,
    user,
    isAuthenticated,
    isInstructor,
    setToken,
    setUser,
    fetchUser,
    clearSession,
    logout,
    loginWithCredentials,
    redirectToLogin,
    consumePostLoginRedirect,
    handleCallback
  }
})
