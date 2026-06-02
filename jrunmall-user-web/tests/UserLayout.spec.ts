import { createPinia, setActivePinia } from 'pinia'
import { mount, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import UserLayout from '@/layouts/UserLayout.vue'
import { useAuthStore } from '@/store/auth'
import { useUserUiStore } from '@/store/ui'

vi.mock('vue-router', async () => {
  const actual = await vi.importActual<typeof import('vue-router')>('vue-router')
  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
    }),
  }
})

describe('UserLayout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders final demo navigation for guest users', () => {
    const uiStore = useUserUiStore()
    uiStore.setCartCount(2)

    const wrapper = mount(UserLayout, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
          RouterView: { template: '<div />' },
        },
      },
    })

    expect(wrapper.text()).toContain('首页')
    expect(wrapper.text()).toContain('商品')
    expect(wrapper.text()).toContain('购物车(2)')
    expect(wrapper.text()).toContain('订单')
    expect(wrapper.text()).toContain('秒杀')
    expect(wrapper.text()).toContain('登录')
    expect(wrapper.text()).toContain('注册')
  })

  it('shows account entry for authenticated users', () => {
    const authStore = useAuthStore()
    authStore.token = 'token-demo'
    authStore.currentUser = {
      userId: 11,
      username: 'jrun_user',
      displayName: 'Jrun User',
    }

    const wrapper = mount(UserLayout, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
          RouterView: { template: '<div />' },
        },
      },
    })

    expect(wrapper.text()).toContain('我的')
    expect(wrapper.text()).toContain('Jrun User')
    expect(wrapper.text()).toContain('退出')
  })
})


