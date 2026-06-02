import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import OrderDetailView from '@/views/orders/OrderDetailView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { orderRef: 'seckill-6' },
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/services/commerce', () => ({
  fetchOrderById: vi.fn(),
  payOrder: vi.fn(),
}))

const commerce = await import('@/services/commerce')

describe('OrderDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(commerce.fetchOrderById).mockResolvedValue({
      orderId: 6,
      orderRef: 'seckill-6',
      orderSn: 'SEC-6',
      userId: 900001,
      username: 'demo-user',
      status: 'CREATED',
      totalAmount: 1999,
      totalQuantity: 1,
      note: '秒杀订单',
      orderSource: 'seckill',
      receiverName: 'Alice',
      receiverPhone: '13800000000',
      receiverAddress: 'Shanghai Pudong Road 1',
      createdTime: '2026-05-01 12:12:22',
      paymentTime: '',
      items: [
        {
          skuId: 14,
          title: 'Jrun Phone 14',
          category: '秒杀专区',
          coverUrl: '/placeholders/products/default-product.svg',
          summary: '来自 Go 秒杀 + Redis Streams + jrunmall-order 的秒杀订单',
          price: 1999,
          quantity: 1,
          lineAmount: 1999,
        },
      ],
    })
  })

  it('renders seckill order detail with the shared pay button', async () => {
    const wrapper = mount(OrderDetailView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('订单详情')
    expect(wrapper.text()).toContain('秒杀订单')
    expect(wrapper.text()).toContain('立即模拟支付')
    expect(commerce.payOrder).not.toHaveBeenCalled()
  })
})


