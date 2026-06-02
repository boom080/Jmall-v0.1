import { describe, expect, it, vi } from 'vitest'

import { orderHttp } from '@/services/orderHttp'
import { fetchMerchantSeckillOrders } from '@/services/merchantSeckillOrders'

describe('merchantSeckillOrders service', () => {
  it('maps backend response data', async () => {
    vi.spyOn(orderHttp, 'get').mockResolvedValue({
      data: {
        code: 0,
        data: [
          {
            orderId: 10,
            orderSn: 'SEC202604291001',
            userId: 900001,
            title: 'Jrunmall 秒杀商品',
            quantity: 1,
            status: 'CREATED',
            source: 'seckill',
            totalAmount: 99,
            createdAt: '2026-04-29 20:00:00',
          },
        ],
      },
    })

    await expect(fetchMerchantSeckillOrders()).resolves.toHaveLength(1)
  })

  it('throws when backend response is not an array', async () => {
    vi.spyOn(orderHttp, 'get').mockResolvedValue({ data: { code: 0, data: {} } })

    await expect(fetchMerchantSeckillOrders()).rejects.toThrow('秒杀订单列表接口返回异常')
  })
})


