import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProductsView from '@/views/products/ProductsView.vue'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push,
  }),
}))

vi.mock('@/services/catalog', () => ({
  fetchCatalogProducts: vi.fn(),
}))

vi.mock('@/services/commerce', () => ({
  addCartItem: vi.fn(),
}))

const catalogService = await import('@/services/catalog')

describe('unauthenticated redirect', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    push.mockReset()
    vi.mocked(catalogService.fetchCatalogProducts).mockResolvedValue({
      source: 'api',
      items: [
        {
          id: 14,
          title: 'Jrun Phone 14',
          category: '手机数码',
          price: 1999,
          coverUrl: '/placeholders/products/default-product.svg',
          imageUrls: ['/placeholders/products/default-product.svg'],
          summary: '轻旗舰手机',
          subtitle: 'subtitle',
          detail: 'detail',
          sellingPoints: [],
          detailAttributes: [],
        },
      ],
    })
  })

  it('redirects to login when unauthenticated user tries to add cart item', async () => {
    const wrapper = mount(ProductsView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          ProductCard: {
            template: '<button class="fake-add" @click="$emit(\'add-to-cart\', 14)">add</button>',
          },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))
    await wrapper.find('.fake-add').trigger('click')

    expect(push).toHaveBeenCalledWith({ name: 'login', query: { redirect: '/products' } })
  })
})


