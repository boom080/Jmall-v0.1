import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createMerchantKnowledgeBase,
  fetchKnowledgeBaseDocuments,
  fetchMerchantKnowledgeBases,
  importKnowledgeBasePdfDocument,
  importKnowledgeBaseTextDocument,
  uploadTxtCreateKnowledgeBase,
} from '@/services/merchantKnowledgeBases'
import { http } from '@/services/http'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('merchantKnowledgeBases service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads merchant knowledge base list with chunk and embedding fields', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: [
          {
            id: 'kb-real',
            label: 'Real Knowledge Base',
            description: 'Uploaded txt knowledge base',
            documentCount: 1,
            chunkCount: 2,
            embeddingStatus: 'embedded:mock-embedding',
            updatedAt: '2026-05-31T10:00:00Z',
            source: 'upload-txt',
          },
        ],
      },
    } as never)

    const result = await fetchMerchantKnowledgeBases()

    expect(result[0].id).toBe('kb-real')
    expect(result[0].chunkCount).toBe(2)
    expect(result[0].embeddingStatus).toBe('embedded:mock-embedding')
    expect(result[0].source).toBe('upload-txt')
  })

  it('creates a knowledge base', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          id: 'kb-real',
          label: 'Real Knowledge Base',
          description: 'Uploaded txt knowledge base',
          documentCount: 0,
          chunkCount: 0,
          embeddingStatus: 'empty',
          updatedAt: '2026-05-31T10:10:00Z',
          source: 'manual',
        },
      },
    } as never)

    const created = await createMerchantKnowledgeBase({
      name: 'Real Knowledge Base',
      description: 'Uploaded txt knowledge base',
    })

    expect(created.id).toBe('kb-real')
    expect(created.embeddingStatus).toBe('empty')
    expect(created.source).toBe('manual')
  })

  it('uploads txt and creates a ready RAG knowledge base', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          knowledgeBaseId: 'kb-real',
          name: 'Real Knowledge Base',
          documentId: 'doc-real',
          chunkCount: 3,
          embeddingProvider: 'mock-embedding',
          status: 'ready',
        },
      },
    } as never)

    const file = new File(['中文商品卖点'], 'real.txt', { type: 'text/plain' })
    const uploaded = await uploadTxtCreateKnowledgeBase({
      name: 'Real Knowledge Base',
      description: 'Uploaded txt knowledge base',
      file,
    })

    expect(http.post).toHaveBeenCalledWith(
      '/product/ai/knowledge-bases/upload-txt',
      expect.any(FormData),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'multipart/form-data',
        }),
      }),
    )
    expect(uploaded.knowledgeBaseId).toBe('kb-real')
    expect(uploaded.documentId).toBe('doc-real')
    expect(uploaded.chunkCount).toBe(3)
    expect(uploaded.embeddingProvider).toBe('mock-embedding')
  })

  it('imports a text document and maps chunk fields', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          id: 'doc-1',
          knowledgeBaseId: 'kb-real',
          title: 'Launch Notes',
          chunkCount: 2,
          embeddingStatus: 'embedded:mock-embedding',
          updatedAt: '2026-05-31T10:20:00Z',
          contentPreview: 'preview',
        },
      },
    } as never)

    const document = await importKnowledgeBaseTextDocument('kb-real', {
      title: 'Launch Notes',
      content: 'Launch content',
    })

    expect(document.chunkCount).toBe(2)
    expect(document.embeddingStatus).toBe('embedded:mock-embedding')
  })

  it('imports a pdf document with multipart payload', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          id: 'doc-pdf',
          knowledgeBaseId: 'kb-real',
          title: 'PDF Notes',
          chunkCount: 3,
          embeddingStatus: 'embedded:mock-embedding',
          updatedAt: '2026-05-31T10:25:00Z',
          contentPreview: 'PDF preview',
        },
      },
    } as never)

    const file = new File(['pdf'], 'demo.pdf', { type: 'application/pdf' })
    const document = await importKnowledgeBasePdfDocument('kb-real', {
      title: 'PDF Notes',
      file,
    })

    expect(http.post).toHaveBeenCalledWith(
      '/product/merchant/knowledge-bases/kb-real/documents/pdf',
      expect.any(FormData),
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'multipart/form-data',
        }),
      }),
    )
    expect(document.id).toBe('doc-pdf')
    expect(document.chunkCount).toBe(3)
  })

  it('throws a friendly error when create response has no data', async () => {
    vi.mocked(http.post).mockResolvedValueOnce({
      data: {
        code: 502,
        msg: 'create failed',
      },
    } as never)

    await expect(
      createMerchantKnowledgeBase({
        name: 'Real Knowledge Base',
        description: 'Uploaded txt knowledge base',
      }),
    ).rejects.toThrow('create failed')
  })

  it('loads knowledge base documents', async () => {
    vi.mocked(http.get).mockResolvedValueOnce({
      data: {
        code: 0,
        msg: 'ok',
        data: [
          {
            id: 'doc-1',
            knowledgeBaseId: 'kb-real',
            title: 'Launch Notes',
            chunkCount: 2,
            embeddingStatus: 'embedded:mock-embedding',
            updatedAt: '2026-05-31T10:20:00Z',
            contentPreview: 'preview',
          },
        ],
      },
    } as never)

    const documents = await fetchKnowledgeBaseDocuments('kb-real')

    expect(documents[0].title).toBe('Launch Notes')
  })
})
