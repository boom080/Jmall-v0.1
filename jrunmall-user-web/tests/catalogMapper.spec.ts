import { describe, expect, it } from 'vitest'

import { mapCatalogCard, mapCatalogDetail, resolveProductCover } from '@/services/catalogMapper'

describe('catalog mapper', () => {
  it('maps real list payload into Jrunmall product shape', () => {
    const product = mapCatalogCard({
      id: 1,
      title: 'Jrun Air 14',
      category: '电脑办公',
      subtitle: '轻薄办公本',
      sellingPoints: ['13代酷睿', '长续航'],
      price: '5699',
      coverUrl: 'http://img.local/1.jpg',
      summary: '真实商品摘要',
    })

    expect(product.title).toBe('Jrun Air 14')
    expect(product.price).toBe(5699)
    expect(product.coverUrl).toBe('http://img.local/1.jpg')
  })

  it('falls back to placeholder image when backend image is empty', () => {
    expect(resolveProductCover('', [])).toBe('/placeholders/products/default-product.svg')
  })

  it('maps detail payload and keeps image fallback chain', () => {
    const product = mapCatalogDetail({
      id: 2,
      title: 'Jrun Fit',
      category: '智能穿戴',
      subtitle: '运动手表',
      sellingPoints: ['全天心率'],
      price: 899,
      coverUrl: '',
      summary: '详情摘要',
      detail: '详情描述',
      imageUrls: ['http://img.local/detail-1.jpg'],
      detailAttributes: ['颜色：黑色'],
    })

    expect(product.coverUrl).toBe('http://img.local/detail-1.jpg')
    expect(product.detailAttributes[0]).toBe('颜色：黑色')
  })
})


