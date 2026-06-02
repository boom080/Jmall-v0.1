import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import OrdersView from '@/views/orders/OrdersView.vue'

vi.mock('@/services/commerce', () => ({
  fetchOrders: vi.fn(),
}))

const commerce = await import('@/services/commerce')

describe('OrdersView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(commerce.fetchOrders).mockResolvedValue([
      {
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
      },
    ])
  })

  it('renders aggregated seckill order list', async () => {
    const wrapper = mount(OrdersView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('我的订单')
    expect(wrapper.text()).toContain('秒杀订单')
    expect(wrapper.text()).toContain('查看详情')
  })
})


