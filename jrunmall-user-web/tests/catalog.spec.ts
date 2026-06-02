import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fallbackProducts } from '@/data/products'
import { fetchCatalogProductById, fetchCatalogProducts } from '@/services/catalog'
import { http } from '@/services/http'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
  },
}))

describe('catalog service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('falls back to local products when backend is unavailable', async () => {
    vi.mocked(http.get).mockRejectedValue(new Error('network'))

    const result = await fetchCatalogProducts()

    expect(result.source).toBe('fallback')
    expect(result.items).toHaveLength(fallbackProducts.length)
    expect(result.errorMessage).toContain('商品列表接口暂时不可用')
  })

  it('maps real product detail payload when api responds successfully', async () => {
    vi.mocked(http.get).mockResolvedValue({
      data: {
        code: 0,
        msg: 'success',
        data: {
          id: 101,
          title: 'Jrun Air 14',
          category: '电脑办公',
          subtitle: '轻薄办公本',
          sellingPoints: ['13代酷睿'],
          price: 5699,
          coverUrl: '',
          summary: '真实商品详情摘要',
          detail: '真实商品详情',
          imageUrls: ['http://img.local/detail.jpg'],
          detailAttributes: ['屏幕：2.8K'],
        },
      },
    })

    const product = await fetchCatalogProductById(String(fallbackProducts[0].id))

    expect(product.product?.title).toBe('Jrun Air 14')
    expect(product.product?.coverUrl).toBe('http://img.local/detail.jpg')
  })
})


