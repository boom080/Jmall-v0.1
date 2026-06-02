import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

import { fetchCurrentUser, loginUser, logoutUser, registerUser } from '@/services/auth'
import { getStoredToken, setStoredToken } from '@/services/http'
import type { CurrentUserProfile, LoginPayload, RegisterPayload } from '@/types/auth'

const USER_KEY = 'jrunmall-user-profile'

function loadStoredUser(): CurrentUserProfile | null {
  if (typeof window === 'undefined') {
    return null
  }
  const raw = window.localStorage.getItem(USER_KEY)
  if (!raw) {
    return null
  }
  try {
    return JSON.parse(raw) as CurrentUserProfile
  } catch {
    return null
  }
}

function persistUser(user: CurrentUserProfile | null) {
  if (typeof window === 'undefined') {
    return
  }
  if (user) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(user))
  } else {
    window.localStorage.removeItem(USER_KEY)
  }
}

export const useAuthStore = defineStore('user-auth', () => {
  const token = ref(getStoredToken())
  const currentUser = ref<CurrentUserProfile | null>(loadStoredUser())
  const loading = ref(false)
  const sessionChecked = ref(false)

  const isAuthenticated = computed(() => Boolean(token.value && currentUser.value?.userId))
  const displayName = computed(() => currentUser.value?.displayName || currentUser.value?.username || '游客')

  async function login(payload: LoginPayload) {
    loading.value = true
    try {
      const response = await loginUser(payload)
      token.value = response.token
      currentUser.value = response.user
      sessionChecked.value = true
      setStoredToken(response.token)
      persistUser(response.user)
      return response.user
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload) {
    loading.value = true
    try {
      await registerUser(payload)
    } finally {
      loading.value = false
    }
  }

  async function refreshCurrentUser() {
    if (!token.value) {
      currentUser.value = null
      persistUser(null)
      sessionChecked.value = true
      return null
    }
    try {
      const user = await fetchCurrentUser()
      currentUser.value = user
      persistUser(user)
      sessionChecked.value = true
      return user
    } catch {
      clear()
      return null
    }
  }

  async function ensureSession() {
    if (!token.value) {
      currentUser.value = null
      persistUser(null)
      sessionChecked.value = true
      return null
    }
    if (sessionChecked.value && currentUser.value?.userId) {
      return currentUser.value
    }
    return refreshCurrentUser()
  }

  async function logout() {
    try {
      if (token.value) {
        await logoutUser()
      }
    } finally {
      clear()
    }
  }

  function clear() {
    token.value = ''
    currentUser.value = null
    sessionChecked.value = true
    setStoredToken('')
    persistUser(null)
  }

  return {
    token,
    currentUser,
    loading,
    sessionChecked,
    isAuthenticated,
    displayName,
    login,
    register,
    refreshCurrentUser,
    ensureSession,
    logout,
    clear,
  }
})


