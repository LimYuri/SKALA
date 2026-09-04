import axios from 'axios'
import { useAuthStore } from '@/store/auth.js'

const api = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

let handlingUnauthorized = false

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      auth.clearSession()

      if (!handlingUnauthorized && !window.location.pathname.startsWith('/login')) {
        handlingUnauthorized = true
        const redirect = `${window.location.pathname}${window.location.search}`
        window.location.replace(`/login?expired=1&redirect=${encodeURIComponent(redirect)}`)
      }
    }
    return Promise.reject(err)
  }
)

export default api
