import { createPinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fallbackProducts } from '@/data/products'
import ProductsView from '@/views/products/ProductsView.vue'

vi.mock('@/services/catalog', () => ({
  fetchCatalogProducts: vi.fn(),
}))

vi.mock('@/services/commerce', () => ({
  addCartItem: vi.fn(),
}))

const { fetchCatalogProducts } = await import('@/services/catalog')

describe('ProductsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders product cards and fallback source label', async () => {
    vi.mocked(fetchCatalogProducts).mockResolvedValue({
      source: 'fallback',
      items: fallbackProducts,
      errorMessage: '商品列表接口暂时不可用，已回退到本地展示数据。',
    })

    const wrapper = mount(ProductsView, {
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

    expect(wrapper.text()).toContain('商品列表')
    expect(wrapper.text()).toContain('本地 fallback')
    expect(wrapper.text()).toContain(fallbackProducts[0].title)
  })
})


