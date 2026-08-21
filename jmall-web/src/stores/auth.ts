import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CurrentUser, LoginPayload, RegisterPayload } from '@/types'
import { authApi } from '@/services/auth'

const TOKEN_KEY = 'jmall-token'
const USER_KEY = 'jmall-user'
const ROLE_KEY = 'jmall-role'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const currentUser = ref<CurrentUser | null>(loadUser())
  const loading = ref(false)
  const sessionChecked = ref(false)
  const role = ref<'shopper' | 'merchant'>(loadRole())

  const isAuthenticated = computed(() => !!token.value && !!currentUser.value)
  const displayName = computed(() => currentUser.value?.nickname || currentUser.value?.username || '未登录')
  const goldBalance = computed(() => currentUser.value?.goldBalance || 0)

  function loadUser(): CurrentUser | null {
    try {
      const stored = localStorage.getItem(USER_KEY)
      return stored ? JSON.parse(stored) : null
    } catch { return null }
  }

  function loadRole(): 'shopper' | 'merchant' {
    return (localStorage.getItem(ROLE_KEY) as 'shopper' | 'merchant') || 'shopper'
  }

  function saveUser(user: CurrentUser) {
    currentUser.value = user
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }

  async function login(payload: LoginPayload) {
    loading.value = true
    try {
      const res = await authApi.login(payload)
      token.value = res.token
      localStorage.setItem(TOKEN_KEY, res.token)
      saveUser(res.user)
      return res.user
    } finally { loading.value = false }
  }

  async function register(payload: RegisterPayload) {
    loading.value = true
    try {
      await authApi.register(payload)
    } finally { loading.value = false }
  }

  async function ensureSession() {
    if (!token.value) { sessionChecked.value = true; return }
    try {
      const user = await authApi.me()
      saveUser(user)
    } catch {
      clear()
    } finally {
      sessionChecked.value = true
    }
  }

  function addGold(amount: number) {
    if (currentUser.value) {
      currentUser.value.goldBalance += amount
      localStorage.setItem(USER_KEY, JSON.stringify(currentUser.value))
    }
  }

  function deductGold(amount: number): boolean {
    if (!currentUser.value || currentUser.value.goldBalance < amount) return false
    currentUser.value.goldBalance -= amount
    localStorage.setItem(USER_KEY, JSON.stringify(currentUser.value))
    return true
  }

  function logout() {
    authApi.logout().catch(() => {})
    clear()
  }

  function clear() {
    token.value = null
    currentUser.value = null
    sessionChecked.value = true
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    token, currentUser, loading, sessionChecked, role,
    isAuthenticated, displayName, goldBalance,
    login, register, ensureSession, addGold, deductGold, logout, clear,
  }
})
