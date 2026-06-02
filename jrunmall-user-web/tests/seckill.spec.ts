import { describe, expect, it, vi } from 'vitest'

import { fetchCurrentSeckillDeal, submitSeckill } from '@/services/seckill'
import { http } from '@/services/http'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('seckill service', () => {
  it('loads current seckill deal without exposing internal ids', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          title: 'Jrun Phone 14',
          category: '手机数码',
          coverUrl: '/placeholders/products/default-product.svg',
          summary: '限时秒杀商品',
          price: 1999,
          limitPerOrder: 1,
        },
      },
    })

    const result = await fetchCurrentSeckillDeal()

    expect(http.get).toHaveBeenCalledWith('/product/user/seckill/current')
    expect(result.title).toBe('Jrun Phone 14')
    expect('skuId' in result).toBe(false)
  })

  it('submits seckill request through Java endpoint', async () => {
    vi.mocked(http.post).mockResolvedValue({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          accepted: true,
          code: 'ACCEPTED',
          message: '抢购成功，请继续确认收货地址并完成支付。',
          quantity: 1,
          orderId: 8,
          orderRef: '8',
          orderSn: 'SEC-8',
        },
      },
    })

    const result = await submitSeckill({ quantity: 1 })

    expect(http.post).toHaveBeenCalledWith('/product/user/seckill/submit', {
      quantity: 1,
    })
    expect(result.accepted).toBe(true)
    expect(result.orderId).toBe(8)
    expect('orderToken' in result).toBe(false)
  })
})


