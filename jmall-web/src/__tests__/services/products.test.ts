import { beforeEach, describe, expect, it, vi } from 'vitest'

const { get, post, put } = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
}))

vi.mock('@/services/http', () => ({ default: { get, post, put } }))

import { productApi } from '@/services/products'

describe('product draft and publish API', () => {
  beforeEach(() => {
    get.mockReset()
    post.mockReset()
    put.mockReset()
  })

  it('uses separate endpoints for check, publish, and unpublish', async () => {
    post.mockResolvedValue({ publishable: false, publish_blockers: [] })

    await productApi.publishCheck(12)
    await productApi.publish(12)
    await productApi.unpublish(12)

    expect(post).toHaveBeenNthCalledWith(1, '/products/12/publish-check')
    expect(post).toHaveBeenNthCalledWith(2, '/products/12/publish')
    expect(post).toHaveBeenNthCalledWith(3, '/products/12/unpublish')
  })

  it('keeps draft persistence on the normal create and update endpoints', async () => {
    post.mockResolvedValue({ id: 12, status: 'draft' })
    put.mockResolvedValue({ id: 12, status: 'draft' })

    await productApi.create({ title: '草稿' })
    await productApi.update(12, { title: '草稿二次编辑' })

    expect(post).toHaveBeenCalledWith('/products', { title: '草稿' })
    expect(put).toHaveBeenCalledWith('/products/12', { title: '草稿二次编辑' })
  })
})
