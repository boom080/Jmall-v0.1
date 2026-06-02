import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AddressesView from '@/views/account/AddressesView.vue'

vi.mock('@/services/addresses', () => ({
  fetchAddresses: vi.fn(),
  createAddress: vi.fn(),
  updateAddress: vi.fn(),
  deleteAddress: vi.fn(),
}))

const addressService = await import('@/services/addresses')

describe('AddressesView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    vi.mocked(addressService.fetchAddresses).mockResolvedValue([
      {
        id: 5,
        name: 'Alice',
        phone: '13800000000',
        province: 'Shanghai',
        city: 'Pudong',
        region: 'Zhangjiang',
        detailAddress: 'Road 1',
        defaultStatus: 1,
      },
    ])
  })

  it('renders address list from service', async () => {
    const wrapper = mount(AddressesView, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('13800000000')
    expect(wrapper.text()).toContain('默认')
  })
})


