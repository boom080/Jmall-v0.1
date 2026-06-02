import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CartView from '@/views/cart/CartView.vue'

vi.mock('@/services/commerce', () => ({
  fetchCartItems: vi.fn(),
  updateCartItem: vi.fn(),
  removeCartItem: vi.fn(),
}))

const commerce = await import('@/services/commerce')

describe('CartView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(commerce.fetchCartItems).mockResolvedValue({
      source: 'api',
      userId: 101,
      displayName: 'Alice',
      totalCount: 1,
      totalAmount: 1999,
      items: [
        {
          skuId: 14,
          title: 'Jrun Phone 14',
          category: '手机数码',
          price: 1999,
          quantity: 1,
          coverUrl: '/placeholders/products/default-product.svg',
          summary: '轻旗舰手机',
          totalAmount: 1999,
        },
      ],
    })
  })

  it('renders cart item from real service payload', async () => {
    const wrapper = mount(CartView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('购物车')
    expect(wrapper.text()).toContain('Jrun Phone 14')
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('去下单')
  })
})


