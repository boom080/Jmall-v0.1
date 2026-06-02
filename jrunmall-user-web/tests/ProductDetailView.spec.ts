import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fallbackProducts } from '@/data/products'
import ProductDetailView from '@/views/products/ProductDetailView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { productId: '101' },
    fullPath: '/products/101',
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/services/catalog', () => ({
  fetchCatalogProductById: vi.fn(),
}))

vi.mock('@/services/commerce', () => ({
  addCartItem: vi.fn(),
}))

const { fetchCatalogProductById } = await import('@/services/catalog')

describe('ProductDetailView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders fallback product detail', async () => {
    vi.mocked(fetchCatalogProductById).mockResolvedValue({
      source: 'fallback',
      product: fallbackProducts[0],
      errorMessage: '商品详情接口暂时不可用，已回退到本地详情数据。',
    })

    const wrapper = mount(ProductDetailView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain(fallbackProducts[0].title)
    expect(wrapper.text()).toContain('加入购物车')
  })
})


