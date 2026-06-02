import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import MerchantSeckillOrdersView from '@/views/seckill-orders/MerchantSeckillOrdersView.vue'

vi.mock('@/services/merchantSeckillOrders', () => ({
  fetchMerchantSeckillOrders: vi.fn(),
}))

const merchantSeckillOrders = await import('@/services/merchantSeckillOrders')

describe('MerchantSeckillOrdersView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(merchantSeckillOrders.fetchMerchantSeckillOrders).mockResolvedValue([
      {
        orderId: 10,
        orderSn: 'SEC202604291001',
        userId: 900001,
        username: 'demo-user',
        skuId: 14,
        title: 'Jrunmall 秒杀商品',
        quantity: 1,
        status: 'CREATED',
        source: 'seckill',
        totalAmount: 99,
        createdAt: '2026-04-29 20:00:00',
      },
    ])
  })

  it('renders read-only seckill orders and source status', async () => {
    const wrapper = mount(MerchantSeckillOrdersView, {
      global: {
        plugins: [ElementPlus],
        stubs: {
          transition: false,
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('秒杀订单只读查看')
    expect(wrapper.text()).toContain('SEC202604291001')
    expect(wrapper.text()).toContain('seckill')
    expect(wrapper.text()).toContain('CREATED')
  })
})


