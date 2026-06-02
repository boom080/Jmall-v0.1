import { mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import KnowledgeBaseView from '@/views/knowledge-base/KnowledgeBaseView.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('@/services/merchantKnowledgeBases', () => ({
  fetchMerchantKnowledgeBases: vi.fn(),
  createMerchantKnowledgeBase: vi.fn(),
  fetchKnowledgeBaseDocuments: vi.fn(),
  importKnowledgeBasePdfDocument: vi.fn(),
  importKnowledgeBaseTextDocument: vi.fn(),
  uploadTxtCreateKnowledgeBase: vi.fn(),
}))

const merchantKnowledgeBases = await import('@/services/merchantKnowledgeBases')

async function flush() {
  await new Promise((resolve) => setTimeout(resolve, 0))
}

function mountView() {
  return mount(KnowledgeBaseView, {
    global: {
      plugins: [ElementPlus],
      stubs: { transition: false },
    },
  })
}

describe('KnowledgeBaseView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(merchantKnowledgeBases.fetchMerchantKnowledgeBases).mockResolvedValue([
      {
        id: 'kb-real',
        label: '真实知识库',
        description: '用户上传 txt 创建',
        documentCount: 1,
        chunkCount: 2,
        embeddingStatus: 'embedded:mock-embedding',
        updatedAt: '2026-05-31T10:00:00Z',
        source: 'upload-txt',
      },
    ])
    vi.mocked(merchantKnowledgeBases.fetchKnowledgeBaseDocuments).mockResolvedValue([
      {
        id: 'doc-real',
        knowledgeBaseId: 'kb-real',
        title: '商品卖点',
        chunkCount: 2,
        embeddingStatus: 'embedded:mock-embedding',
        updatedAt: '2026-05-31T10:20:00Z',
        contentPreview: '中文商品卖点',
      },
    ])
    vi.mocked(merchantKnowledgeBases.importKnowledgeBasePdfDocument).mockResolvedValue({
      id: 'doc-pdf',
      knowledgeBaseId: 'kb-real',
      title: 'PDF Notes',
      chunkCount: 2,
      embeddingStatus: 'embedded:mock-embedding',
      updatedAt: '2026-05-31T10:21:00Z',
      contentPreview: 'PDF preview',
    })
    vi.mocked(merchantKnowledgeBases.uploadTxtCreateKnowledgeBase).mockResolvedValue({
      knowledgeBaseId: 'kb-real',
      name: '真实知识库',
      documentId: 'doc-real',
      chunkCount: 2,
      embeddingProvider: 'mock-embedding',
      status: 'ready',
    })
  })

  it('renders upload form, knowledge base list, and document table', async () => {
    const wrapper = mountView()

    await flush()
    await flush()

    expect(wrapper.text()).toContain('上传 txt 创建真实知识库')
    expect(wrapper.text()).toContain('真实知识库')
    expect(wrapper.text()).toContain('商品卖点')
  })

  it('uploads txt, creates a knowledge base, and refreshes the list', async () => {
    const wrapper = mountView()

    await flush()
    await flush()

    const inputs = wrapper.findAll('input')
    await inputs[0].setValue('真实知识库')
    await inputs[1].setValue('用于商品文案')

    const txtInput = wrapper.find('input[accept="text/plain,.txt"]')
    const file = new File(['中文商品卖点'], 'real.txt', { type: 'text/plain' })
    Object.defineProperty(txtInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await txtInput.trigger('change')

    await wrapper.findAll('button').find((item) => item.text().includes('上传 txt 创建知识库'))?.trigger('click')
    await flush()
    await flush()

    expect(merchantKnowledgeBases.uploadTxtCreateKnowledgeBase).toHaveBeenCalledWith({
      name: '真实知识库',
      description: '用于商品文案',
      file,
    })
    expect(merchantKnowledgeBases.fetchMerchantKnowledgeBases).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('已创建知识库：真实知识库，Chunk 数：2')
  })

  it('shows empty state when no real knowledge bases exist', async () => {
    vi.mocked(merchantKnowledgeBases.fetchMerchantKnowledgeBases).mockResolvedValueOnce([])

    const wrapper = mountView()

    await flush()
    await flush()

    expect(wrapper.text()).toContain('暂无知识库，请上传 txt 创建')
  })

  it('imports a pdf document for the selected knowledge base', async () => {
    const wrapper = mountView()

    await flush()
    await flush()

    const pdfInput = wrapper.find('input[accept="application/pdf,.pdf"]')
    const file = new File(['pdf'], 'demo.pdf', { type: 'application/pdf' })
    Object.defineProperty(pdfInput.element, 'files', {
      value: [file],
      configurable: true,
    })
    await pdfInput.trigger('change')
    await wrapper.findAll('button').find((item) => item.text().includes('导入 PDF'))?.trigger('click')
    await flush()

    expect(merchantKnowledgeBases.importKnowledgeBasePdfDocument).toHaveBeenCalledWith('kb-real', {
      title: 'demo.pdf',
      file,
    })
  })
})
