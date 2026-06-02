import { createPinia, setActivePinia } from 'pinia'
import { mount, RouterLinkStub } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import MerchantLayout from '@/layouts/MerchantLayout.vue'

vi.mock('vue-router', async () => {
  const actual = await vi.importActual<typeof import('vue-router')>('vue-router')
  return {
    ...actual,
    useRoute: () => ({
      meta: {
        title: '商品管理',
      },
    }),
  }
})

describe('MerchantLayout', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders production merchant navigation entries', () => {
    const wrapper = mount(MerchantLayout, {
      global: {
        stubs: {
          RouterLink: RouterLinkStub,
          RouterView: { template: '<div />' },
        },
      },
    })

    expect(wrapper.text()).toContain('Jrunmall Merchant')
    expect(wrapper.text()).not.toContain('演示总览')
    expect(wrapper.text()).toContain('商品管理')
    expect(wrapper.text()).toContain('知识库管理')
    expect(wrapper.text()).not.toContain('商品 AI 工作台')
    expect(wrapper.text()).toContain('普通订单')
    expect(wrapper.text()).toContain('秒杀订单')
  })
})
