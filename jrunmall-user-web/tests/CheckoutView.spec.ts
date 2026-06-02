import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import CheckoutView from '@/views/checkout/CheckoutView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: {},
  }),
  useRouter: () => ({
    push,
  }),
}))

vi.mock('@/services/commerce', () => ({
  fetchCartItems: vi.fn(),
  fetchOrderById: vi.fn(),
  createOrder: vi.fn(),
  confirmOrderAddress: vi.fn(),
}))

vi.mock('@/services/addresses', () => ({
  fetchAddresses: vi.fn(),
}))

const commerce = await import('@/services/commerce')
const addresses = await import('@/services/addresses')

describe('CheckoutView', () => {
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
    vi.mocked(addresses.fetchAddresses).mockResolvedValue([
      {
        id: 5,
        name: 'Alice',
        phone: '13800000000',
        province: 'Shanghai',
        city: 'Pudong',
        region: 'Zhangjiang',
        detailAddress: 'Road 1',
        defaultStatus: 1,
      },
    ])
    vi.mocked(commerce.createOrder).mockResolvedValue({
      orderId: 1,
      orderSn: '202604270001',
      userId: 101,
      username: 'alice',
      status: 'CREATED',
      totalAmount: 1999,
      totalQuantity: 1,
      note: '',
      addressId: 5,
      receiverName: 'Alice',
      receiverPhone: '13800000000',
      receiverAddress: 'Shanghai Pudong Zhangjiang Road 1',
      createdTime: '2026-04-27 21:00:00',
      paymentTime: '',
      items: [],
    })
  })

  it('submits order with selected address and navigates to order detail', async () => {
    const wrapper = mount(CheckoutView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))
    const button = wrapper.find('button.primary-link')
    await button.trigger('click')

    expect(commerce.createOrder).toHaveBeenCalledWith(5, '')
    expect(push).toHaveBeenCalledWith('/orders/1')
  })
})


