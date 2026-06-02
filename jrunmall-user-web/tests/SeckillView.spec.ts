import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import SeckillView from '@/views/seckill/SeckillView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push,
  }),
}))

vi.mock('@/services/seckill', () => ({
  fetchCurrentSeckillDeal: vi.fn().mockResolvedValue({
    title: 'Jrun Phone 14',
    category: '手机数码',
    coverUrl: '/placeholders/products/default-product.svg',
    summary: '限时秒杀商品',
    price: 1999,
    limitPerOrder: 1,
  }),
  submitSeckill: vi.fn().mockResolvedValue({
    accepted: true,
    code: 'ACCEPTED',
    message: '抢购成功，请继续确认收货地址并完成支付。',
    quantity: 1,
    orderId: 8,
    orderRef: '8',
    orderSn: 'SEC-8',
  }),
}))

describe('SeckillView', () => {
  it('renders accepted seckill result', async () => {
    const wrapper = mount(SeckillView, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))
    await wrapper.find('button.primary-link').trigger('click')
    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('Jrun Phone 14')
    expect(wrapper.text()).not.toContain('flash-20260429')
    expect(wrapper.text()).not.toContain('SEC-8')
    expect(push).toHaveBeenCalledWith({ name: 'checkout', query: { seckillOrderId: '8' } })
  })
})


