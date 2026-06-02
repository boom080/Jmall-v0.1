import axios from 'axios'

const AUTH_TOKEN_KEY = 'jrunmall-user-token'

export function getStoredToken(): string {
  if (typeof window === 'undefined') {
    return ''
  }
  return window.localStorage.getItem(AUTH_TOKEN_KEY) || ''
}

export function setStoredToken(token: string) {
  if (typeof window === 'undefined') {
    return
  }
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token)
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_KEY)
  }
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 5000,
})

http.interceptors.request.use((config) => {
  const token = getStoredToken()
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})


