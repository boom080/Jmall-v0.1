import { describe, expect, it } from 'vitest'

import { mapCartSnapshot, mapOrder, resolveProductImage } from '@/services/commerceMapper'

describe('commerce mapper', () => {
  it('falls back to placeholder image when backend cover is empty', () => {
    expect(resolveProductImage('')).toBe('/placeholders/products/default-product.svg')
  })

  it('maps cart payload into user facing snapshot', () => {
    const snapshot = mapCartSnapshot({
      userId: 101,
      displayName: 'Alice',
      totalCount: 2,
      totalAmount: 3998,
      items: [
        {
          skuId: 14,
          title: 'Jrun Phone 14',
          category: '手机数码',
          price: 1999,
          quantity: 2,
          coverUrl: '',
          summary: '轻旗舰手机',
          totalAmount: 3998,
        },
      ],
    })

    expect(snapshot.displayName).toBe('Alice')
    expect(snapshot.items[0].coverUrl).toBe('/placeholders/products/default-product.svg')
    expect(snapshot.totalAmount).toBe(3998)
  })

  it('maps order payload and keeps address snapshot', () => {
    const order = mapOrder({
      orderId: 1,
      orderSn: '202604270001',
      userId: 101,
      username: 'alice',
      status: 'PAID',
      totalAmount: 1999,
      totalQuantity: 1,
      note: '',
      addressId: 5,
      receiverName: 'Alice',
      receiverPhone: '13800000000',
      receiverAddress: 'Shanghai Road 1',
      createdTime: '2026-04-27 21:00:00',
      paymentTime: '2026-04-27 21:01:00',
      items: [],
    })

    expect(order.status).toBe('PAID')
    expect(order.receiverAddress).toContain('Shanghai')
  })
})


