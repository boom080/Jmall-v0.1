import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/store/auth'

vi.mock('@/services/auth', () => ({
  loginUser: vi.fn(),
  registerUser: vi.fn(),
  fetchCurrentUser: vi.fn(),
  logoutUser: vi.fn(),
}))

const authService = await import('@/services/auth')

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    window.localStorage.clear()
    vi.clearAllMocks()
  })

  it('stores token and user after login', async () => {
    vi.mocked(authService.loginUser).mockResolvedValue({
      token: 'token-1',
      user: {
        userId: 101,
        username: 'alice',
        displayName: 'Alice',
      },
    })

    const store = useAuthStore()
    await store.login({
      loginacct: 'alice',
      password: '123456',
    })

    expect(store.isAuthenticated).toBe(true)
    expect(store.displayName).toBe('Alice')
    expect(store.sessionChecked).toBe(true)
  })

  it('clears stale persisted user when token validation fails', async () => {
    window.localStorage.setItem('jrunmall-user-token', 'stale-token')
    window.localStorage.setItem(
      'jrunmall-user-profile',
      JSON.stringify({
        userId: 101,
        username: 'alice',
        displayName: 'Alice',
      }),
    )
    vi.mocked(authService.fetchCurrentUser).mockRejectedValue(new Error('请先登录'))

    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)

    await store.ensureSession()

    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBe('')
    expect(window.localStorage.getItem('jrunmall-user-token')).toBeNull()
    expect(window.localStorage.getItem('jrunmall-user-profile')).toBeNull()
  })
})


