import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ProductManagementView from '@/views/products/ProductManagementView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({
    query: {},
  }),
}))

vi.mock('@/services/merchantProducts', () => ({
  createMerchantProduct: vi.fn(),
  fetchMerchantProducts: vi.fn(),
  fetchMerchantProductDetail: vi.fn(),
  updateMerchantProduct: vi.fn(),
  uploadMerchantProductImage: vi.fn(),
}))

vi.mock('@/services/merchantAi', () => {
  class MerchantAiValidationError extends Error {
    fieldErrors: Record<string, string>

    constructor(message: string, fieldErrors: Record<string, string>) {
      super(message)
      this.fieldErrors = fieldErrors
    }
  }

  return {
    MerchantAiValidationError,
    fetchAiModels: vi.fn(),
    fetchKnowledgeBases: vi.fn(),
    generateMerchantProductCopy: vi.fn(),
  }
})

const merchantProducts = await import('@/services/merchantProducts')
const merchantAi = await import('@/services/merchantAi')

async function flush() {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

function mountView() {
  return mount(ProductManagementView, {
    global: {
      plugins: [ElementPlus],
      stubs: {
        transition: false,
      },
    },
  })
}

describe('ProductManagementView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(merchantProducts.fetchMerchantProducts).mockResolvedValue({
      source: 'api',
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
    })
    vi.mocked(merchantProducts.fetchMerchantProductDetail).mockResolvedValue({
      id: 14,
      title: 'Jrun Phone 14',
      category: '手机数码',
      price: 1999,
      sellingPoints: ['轻旗舰'],
      coverUrl: '',
      status: 'ready',
    })
    vi.mocked(merchantAi.fetchAiModels).mockResolvedValue([
      {
        id: 'mock:mock-product-copy-v1',
        label: 'Mock / mock-product-copy-v1',
        provider: 'mock',
      },
    ])
    vi.mocked(merchantAi.fetchKnowledgeBases).mockResolvedValue([
      {
        id: 'kb-real',
        label: '真实知识库',
        description: '商品知识',
        documentCount: 1,
        chunkCount: 2,
      },
    ])
  })

  it('renders product list with listing actions and create entry', async () => {
    const wrapper = mountView()

    await flush()

    expect(wrapper.text()).toContain('商品列表')
    expect(wrapper.text()).toContain('Jrun Phone 14')
    expect(wrapper.text()).toContain('1999')
    expect(wrapper.text()).toContain('新增商品')
    expect(wrapper.text()).toContain('编辑')
    expect(wrapper.text()).toContain('下架')
    expect(wrapper.text()).not.toContain('商品 AI 工作台')
  })

  it('creates a product from the product dialog', async () => {
    vi.mocked(merchantProducts.createMerchantProduct).mockResolvedValue({
      id: 88,
      title: 'Jrun Pad Air',
      category: '手机数码',
      price: 1299,
      sellingPoints: ['轻薄'],
      coverUrl: '',
      status: 'ready',
    })

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('新增商品'))?.trigger('click')
    await flush()

    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('Jrun Pad Air')
    await inputs[1].setValue('手机数码')
    await inputs[2].setValue('1299')
    await wrapper.find('textarea').setValue('轻薄')
    await wrapper.findAll('button').find((item) => item.text().includes('创建商品'))?.trigger('click')
    await flush()

    expect(merchantProducts.createMerchantProduct).toHaveBeenCalledWith({
      title: 'Jrun Pad Air',
      category: '手机数码',
      price: 1299,
      sellingPoints: ['轻薄'],
      coverUrl: '',
      status: 'ready',
    })
    expect(wrapper.text()).toContain('商品已新增')
  })

  it('opens editor and validates title before save', async () => {
    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('编辑'))?.trigger('click')
    await flush()

    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('')
    await wrapper.findAll('button').find((item) => item.text().includes('保存'))?.trigger('click')

    expect(wrapper.text()).toContain('商品标题不能为空')
  })

  it('shows success message after save', async () => {
    vi.mocked(merchantProducts.updateMerchantProduct).mockResolvedValue({
      id: 14,
      title: 'Jrun Phone 14 Pro',
      category: '手机数码',
      price: 2999,
      sellingPoints: ['轻旗舰', '长续航'],
      coverUrl: '',
      status: 'ready',
    })

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('编辑'))?.trigger('click')
    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('保存'))?.trigger('click')
    await flush()

    expect(wrapper.text()).toContain('商品已保存')
  })

  it('generates copy inside the product dialog and applies successful result', async () => {
    vi.mocked(merchantAi.generateMerchantProductCopy).mockResolvedValue({
      generatedTitle: 'Jrun Phone 14 AI 标题',
      highlights: ['AI 轻旗舰', 'AI 长续航'],
      summary: '适合主推',
      provider: 'mock',
      mock: false,
      success: true,
      message: 'ok',
    })

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('编辑'))?.trigger('click')
    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('生成文案'))?.trigger('click')
    await flush()

    expect(merchantAi.generateMerchantProductCopy).toHaveBeenCalledWith({
      title: 'Jrun Phone 14',
      category: '手机数码',
      sellingPoints: ['轻旗舰'],
      tone: 'professional',
      modelProvider: 'mock',
      modelName: 'mock-product-copy-v1',
      knowledgeBaseId: 'kb-real',
    })

    await wrapper.findAll('button').find((item) => item.text().includes('回填标题和卖点'))?.trigger('click')
    await flush()

    expect((wrapper.findAll('input')[0].element as HTMLInputElement).value).toBe('Jrun Phone 14 AI 标题')
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toContain('AI 轻旗舰')
  })

  it('prefers DeepSeek over Qwen and mock when selecting the default AI model', async () => {
    vi.mocked(merchantAi.fetchAiModels).mockResolvedValueOnce([
      {
        id: 'langchain4j-openai:qwen3-max',
        label: 'Qwen / qwen3-max',
        provider: 'langchain4j-openai',
      },
      {
        id: 'mock:mock-product-copy-v1',
        label: 'Mock / mock-product-copy-v1',
        provider: 'mock',
      },
      {
        id: 'langchain4j-openai:deepseek-chat',
        label: 'DeepSeek / deepseek-chat',
        provider: 'langchain4j-openai',
      },
    ])
    vi.mocked(merchantAi.generateMerchantProductCopy).mockResolvedValue({
      generatedTitle: 'Jrun Phone 14 AI',
      highlights: ['AI highlight'],
      summary: 'ok',
      provider: 'langchain4j-openai:deepseek-chat',
      mock: false,
      success: true,
      message: 'ok',
    })

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('编辑'))?.trigger('click')
    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('生成文案'))?.trigger('click')
    await flush()

    expect(merchantAi.generateMerchantProductCopy).toHaveBeenCalledWith({
      title: 'Jrun Phone 14',
      category: '手机数码',
      sellingPoints: ['轻旗舰'],
      tone: 'professional',
      modelProvider: 'langchain4j-openai',
      modelName: 'deepseek-chat',
      knowledgeBaseId: 'kb-real',
    })
  })

  it('toggles product listing status from the table', async () => {
    vi.mocked(merchantProducts.updateMerchantProduct).mockResolvedValue({
      id: 14,
      title: 'Jrun Phone 14',
      category: '手机数码',
      price: 1999,
      sellingPoints: ['轻旗舰'],
      coverUrl: '',
      status: 'draft',
    })

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('下架'))?.trigger('click')
    await flush()

    expect(merchantProducts.updateMerchantProduct).toHaveBeenCalledWith(14, {
      title: 'Jrun Phone 14',
      category: '手机数码',
      price: 1999,
      sellingPoints: ['轻旗舰'],
      coverUrl: '',
      status: 'draft',
    })
    expect(wrapper.text()).toContain('商品已下架')
  })

  it('shows error message when save fails', async () => {
    vi.mocked(merchantProducts.updateMerchantProduct).mockRejectedValue(new Error('商品保存失败'))

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('编辑'))?.trigger('click')
    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('保存'))?.trigger('click')
    await flush()

    expect(wrapper.text()).toContain('商品保存失败')
  })

  it('fills coverUrl after image upload succeeds', async () => {
    vi.mocked(merchantProducts.uploadMerchantProductImage).mockResolvedValue({
      objectKey: 'merchant-products/demo.png',
      url: 'https://cdn.example.com/merchant-products/demo.png',
    })

    const wrapper = mountView()

    await flush()
    await wrapper.findAll('button').find((item) => item.text().includes('编辑'))?.trigger('click')
    await flush()

    const input = wrapper.find('input[type="file"]')
    const file = new File(['demo'], 'demo.png', { type: 'image/png' })
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true,
    })
    await input.trigger('change')
    await flush()

    expect(wrapper.text()).toContain('图片上传成功')
  })
})
