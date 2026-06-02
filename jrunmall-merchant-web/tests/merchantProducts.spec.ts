import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createMerchantProduct,
  fetchMerchantProductDetail,
  fetchMerchantProducts,
  updateMerchantProduct,
  uploadMerchantProductImage,
} from '@/services/merchantProducts'
import { http } from '@/services/http'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn(),
  },
}))

describe('merchantProducts service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('maps empty cover image to placeholder', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          items: [
            {
              id: 14,
              title: 'Jrun Phone 14',
              category: '手机数码',
              price: 1999,
              sellingPoints: ['轻旗舰'],
              coverUrl: '',
              status: 'ready',
            },
          ],
        },
      },
    } as never)

    const result = await fetchMerchantProducts()

    expect(result.source).toBe('api')
    expect(result.items[0].coverUrl).toBe('/placeholders/products/default-product.svg')
  })

  it('loads merchant product detail', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          id: 14,
          title: 'Jrun Phone 14',
          category: '手机数码',
          price: 1999,
          sellingPoints: ['轻旗舰'],
          coverUrl: '',
          status: 'ready',
        },
      },
    } as never)

    const detail = await fetchMerchantProductDetail(14)

    expect(detail.id).toBe(14)
    expect(detail.coverUrl).toBe('/placeholders/products/default-product.svg')
  })

  it('updates merchant product and returns normalized payload', async () => {
    vi.mocked(http.put).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          id: 14,
          title: 'Jrun Phone 14 Pro',
          category: '手机数码',
          price: 2999,
          sellingPoints: ['轻旗舰', '长续航'],
          coverUrl: '',
          status: 'ready',
        },
      },
    } as never)

    const updated = await updateMerchantProduct(14, {
      title: 'Jrun Phone 14 Pro',
      category: '手机数码',
      price: 2999,
      sellingPoints: ['轻旗舰', '长续航'],
      coverUrl: '',
      status: 'ready',
    })

    expect(updated.title).toBe('Jrun Phone 14 Pro')
    expect(updated.coverUrl).toBe('/placeholders/products/default-product.svg')
  })

  it('creates merchant product and returns normalized payload', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          id: 88,
          title: 'Jrun Pad Air',
          category: '手机数码',
          price: 1299,
          sellingPoints: ['轻薄'],
          coverUrl: '',
          status: 'draft',
        },
      },
    } as never)

    const created = await createMerchantProduct({
      title: 'Jrun Pad Air',
      category: '手机数码',
      price: 1299,
      sellingPoints: ['轻薄'],
      coverUrl: '',
      status: 'draft',
    })

    expect(http.post).toHaveBeenCalledWith('/product/merchant/products', {
      title: 'Jrun Pad Air',
      category: '手机数码',
      price: 1299,
      sellingPoints: ['轻薄'],
      coverUrl: '',
      status: 'draft',
    })
    expect(created.id).toBe(88)
    expect(created.coverUrl).toBe('/placeholders/products/default-product.svg')
  })

  it('uploads product image and returns response payload', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          objectKey: 'merchant-products/demo.png',
          url: 'https://cdn.example.com/merchant-products/demo.png',
        },
      },
    } as never)

    const file = new File(['demo'], 'demo.png', { type: 'image/png' })
    const uploaded = await uploadMerchantProductImage(file)

    expect(uploaded.objectKey).toBe('merchant-products/demo.png')
    expect(uploaded.url).toContain('cdn.example.com')
  })
})


