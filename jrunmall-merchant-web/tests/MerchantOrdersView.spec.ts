import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import MerchantOrdersView from '@/views/orders/MerchantOrdersView.vue'

vi.mock('@/services/merchantOrders', () => ({
  fetchMerchantOrders: vi.fn(),
}))

const merchantOrders = await import('@/services/merchantOrders')

describe('MerchantOrdersView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(merchantOrders.fetchMerchantOrders).mockResolvedValue([
      {
        orderId: 1,
        orderSn: '202604270001',
        userId: 900001,
        username: 'jrunmall_demo',
        status: 'PAID',
        totalAmount: 1999,
        totalQuantity: 1,
        createdTime: '2026-04-27 21:00:00',
        paymentTime: '2026-04-27 21:01:00',
      },
    ])
  })

  it('renders merchant order list and status', async () => {
    const wrapper = mount(MerchantOrdersView, {
      global: {
        plugins: [ElementPlus],
        stubs: {
          transition: false,
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('用户端订单列表')
    expect(wrapper.text()).toContain('202604270001')
    expect(wrapper.text()).toContain('PAID')
  })
})


