import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createOrder, fetchCartItems, fetchOrderById, fetchOrders, payOrder } from '@/services/commerce'
import { http } from '@/services/http'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

describe('commerce services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('maps cart payload from backend contract', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
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
              coverUrl: '',
              summary: '轻旗舰手机',
              totalAmount: 1999,
            },
          ],
        },
      },
    } as never)

    const result = await fetchCartItems()

    expect(result.source).toBe('api')
    expect(result.displayName).toBe('Alice')
    expect(result.items[0].coverUrl).toBe('/placeholders/products/default-product.svg')
  })

  it('sends addressId when creating order', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          orderId: 1,
          orderSn: 'NORMAL-1',
          userId: 101,
          username: 'alice',
          status: 'CREATED',
          totalAmount: 88,
          totalQuantity: 1,
          note: '',
          addressId: 5,
          receiverName: 'Alice',
          receiverPhone: '13800000000',
          receiverAddress: 'Shanghai Pudong Road 1',
          createdTime: '2026-05-04T10:00:00.000+0000',
          items: [],
        },
      },
    } as never)

    await createOrder(5, 'note')

    expect(http.post).toHaveBeenCalledWith('/product/user/orders', { addressId: 5, note: 'note' })
  })

  it('loads unified order list from backend aggregation endpoint', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: [
          {
            orderId: 6,
            orderRef: 'seckill-6',
            orderSn: 'SEC-6',
            userId: 101,
            username: 'alice',
            status: 'CREATED',
            totalAmount: 1999,
            totalQuantity: 1,
            note: 'seckill order',
            orderSource: 'seckill',
            createdTime: '2026-05-01T12:12:22.000+0000',
            items: [],
          },
          {
            orderId: 1,
            orderRef: '1',
            orderSn: 'NORMAL-1',
            userId: 101,
            username: 'alice',
            status: 'PAID',
            totalAmount: 88,
            totalQuantity: 1,
            note: '',
            orderSource: 'normal',
            createdTime: '2026-05-01T11:00:00.000+0000',
            paymentTime: '2026-05-01T11:02:00.000+0000',
            items: [],
          },
        ],
      },
    } as never)

    const orders = await fetchOrders()

    expect(orders).toHaveLength(2)
    expect(orders[0].orderSource).toBe('seckill')
    expect(orders[0].orderRef).toBe('seckill-6')
    expect(orders[1].orderRef).toBe('1')
  })

  it('loads unified detail by source-aware orderRef route', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          orderId: 6,
          orderRef: 'seckill-6',
          orderSn: 'SEC-6',
          userId: 101,
          username: 'alice',
          status: 'CREATED',
          totalAmount: 1999,
          totalQuantity: 1,
          note: 'seckill order',
          orderSource: 'seckill',
          createdTime: '2026-05-01T12:12:22.000+0000',
          items: [],
        },
      },
    } as never)

    const order = await fetchOrderById('seckill-6')

    expect(order.orderSource).toBe('seckill')
    expect(order.orderRef).toBe('seckill-6')
  })

  it('maps pay order result to paid status', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          orderId: 1,
          orderSn: '202604270001',
          userId: 101,
          username: 'alice',
          status: 'PAID',
          totalAmount: 1999,
          totalQuantity: 1,
          note: '',
          createdTime: '2026-04-27 21:00:00',
          paymentTime: '2026-04-27 21:01:00',
          items: [],
        },
      },
    } as never)

    const order = await payOrder(1)

    expect(order.status).toBe('PAID')
  })
})


