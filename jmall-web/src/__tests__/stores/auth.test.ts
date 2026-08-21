/** Tests for the auth Pinia store.
 *
 * Covers: login, register, logout, gold operations, session handling,
 * localStorage persistence, computed properties.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { mockFetch } from '../setup'

// Mock the auth API module
vi.mock('@/services/auth', () => ({
  authApi: {
    login: vi.fn(),
    register: vi.fn(),
    me: vi.fn(),
    logout: vi.fn(),
  },
}))

import { authApi } from '@/services/auth'

function mockLoginResponse() {
  return {
    token: 'test-jwt-token',
    user: {
      id: 1,
      username: 'testuser',
      nickname: '测试用户',
      role: 'user' as const,
      goldBalance: 10000,
      pointsBalance: 500,
      checkinStreak: 3,
    },
  }
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts unauthenticated', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
    })

    it('has default role as shopper', () => {
      const store = useAuthStore()
      expect(store.role).toBe('shopper')
    })

    it('has zero gold balance when not logged in', () => {
      const store = useAuthStore()
      expect(store.goldBalance).toBe(0)
    })

    it('displayName defaults to 未登录', () => {
      const store = useAuthStore()
      expect(store.displayName).toBe('未登录')
    })
  })

  describe('login', () => {
    it('sets token and user on successful login', async () => {
      const response = mockLoginResponse()
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'testuser', password: 'pass123' })

      expect(store.isAuthenticated).toBe(true)
      expect(store.token).toBe('test-jwt-token')
      expect(store.currentUser?.username).toBe('testuser')
      expect(localStorage.getItem('jmall-token')).toBe('test-jwt-token')
    })

    it('updates gold balance from API response', async () => {
      const response = mockLoginResponse()
      response.user.goldBalance = 50000
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'rich', password: 'pass' })

      expect(store.goldBalance).toBe(50000)
    })

    it('persists user to localStorage', async () => {
      const response = mockLoginResponse()
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'testuser', password: 'pass' })

      const stored = JSON.parse(localStorage.getItem('jmall-user')!)
      expect(stored.username).toBe('testuser')
      expect(stored.goldBalance).toBe(10000)
    })
  })

  describe('register', () => {
    it('calls register API without setting auth state', async () => {
      vi.mocked(authApi.register).mockResolvedValue(undefined)

      const store = useAuthStore()
      await store.register({ username: 'newuser', password: 'pass', nickname: '新人' })

      expect(authApi.register).toHaveBeenCalledWith({
        username: 'newuser',
        password: 'pass',
        nickname: '新人',
      })
      // Register should NOT set token
      expect(store.isAuthenticated).toBe(false)
    })
  })

  describe('gold operations', () => {
    it('addGold increases balance', async () => {
      const response = mockLoginResponse()
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'test', password: 'pass' })

      store.addGold(500)
      expect(store.goldBalance).toBe(10500)
    })

    it('deductGold decreases balance when sufficient', async () => {
      const response = mockLoginResponse()
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'test', password: 'pass' })

      const ok = store.deductGold(3000)
      expect(ok).toBe(true)
      expect(store.goldBalance).toBe(7000)
    })

    it('deductGold returns false when insufficient funds', async () => {
      const response = mockLoginResponse()
      response.user.goldBalance = 100
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'poor', password: 'pass' })

      const ok = store.deductGold(500)
      expect(ok).toBe(false)
      expect(store.goldBalance).toBe(100) // Unchanged
    })

    it('deductGold returns false when not logged in', () => {
      const store = useAuthStore()
      const ok = store.deductGold(100)
      expect(ok).toBe(false)
    })
  })

  describe('logout', () => {
    it('clears token, user, and localStorage', async () => {
      const response = mockLoginResponse()
      vi.mocked(authApi.login).mockResolvedValue(response)
      vi.mocked(authApi.logout).mockResolvedValue(undefined)

      const store = useAuthStore()
      await store.login({ username: 'test', password: 'pass' })
      expect(store.isAuthenticated).toBe(true)

      store.logout()
      expect(store.isAuthenticated).toBe(false)
      expect(store.token).toBeNull()
      expect(store.currentUser).toBeNull()
      expect(localStorage.getItem('jmall-token')).toBeNull()
    })
  })

  describe('displayName', () => {
    it('returns nickname when available', async () => {
      const response = mockLoginResponse()
      response.user.nickname = '小明'
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'test', password: 'pass' })

      expect(store.displayName).toBe('小明')
    })

    it('falls back to username when no nickname', async () => {
      const response = mockLoginResponse()
      response.user.nickname = ''
      vi.mocked(authApi.login).mockResolvedValue(response)

      const store = useAuthStore()
      await store.login({ username: 'testuser', password: 'pass' })

      expect(store.displayName).toBe('testuser')
    })
  })
})
