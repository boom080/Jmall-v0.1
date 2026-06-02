import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import LoginView from '@/views/auth/LoginView.vue'
import RegisterView from '@/views/auth/RegisterView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push,
  }),
  useRoute: () => ({
    query: {},
  }),
}))

describe('auth pages', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockReset()
  })

  it('renders login form', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    expect(wrapper.text()).toContain('登录 Jrunmall 用户端')
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
  })

  it('renders register form', () => {
    const wrapper = mount(RegisterView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    expect(wrapper.text()).toContain('创建 Jrunmall 用户')
    expect(wrapper.findAll('input').length).toBeGreaterThanOrEqual(3)
  })
})


