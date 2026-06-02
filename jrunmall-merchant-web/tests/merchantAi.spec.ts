import { beforeEach, describe, expect, it, vi } from 'vitest'

import { fallbackModels } from '@/data/fallbackProducts'
import { fetchAiModels, fetchKnowledgeBases, generateMerchantProductCopy, MerchantAiValidationError } from '@/services/merchantAi'
import { http } from '@/services/http'

vi.mock('@/services/http', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

vi.mock('@/services/merchantKnowledgeBases', () => ({
  fetchKnowledgeBaseOptions: vi.fn(),
}))

const merchantKnowledgeBases = await import('@/services/merchantKnowledgeBases')

describe('merchant ai services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('falls back to local models when backend list is unavailable', async () => {
    vi.mocked(http.get).mockRejectedValue(new Error('network'))

    const models = await fetchAiModels()

    expect(models).toEqual(fallbackModels)
  })

  it('returns no knowledge bases when backend list is unavailable', async () => {
    vi.mocked(merchantKnowledgeBases.fetchKnowledgeBaseOptions).mockRejectedValue(new Error('network'))

    const items = await fetchKnowledgeBases()

    expect(items).toEqual([])
  })

  it('exports a validation error type for form mapping', () => {
    const error = new MerchantAiValidationError('invalid', { title: 'title is required' })

    expect(error.fieldErrors.title).toBe('title is required')
  })

  it('sends knowledgeBaseId and returns RAG result fields', async () => {
    vi.mocked(http.post).mockResolvedValue({
      data: {
        code: 0,
        msg: 'ok',
        data: {
          generatedTitle: 'Jrun Air 14 RAG title',
          highlights: ['portable'],
          summary: 'mock summary',
          provider: 'qwen-plus',
          mock: false,
          success: true,
          message: 'ok',
          response_source: 'rag',
          embeddingProvider: 'mock-embedding',
          usedChunks: [
            {
              chunkId: 'chunk-real-0',
              documentId: 'doc-real',
              knowledgeBaseId: 'kb-real',
              content: 'reference chunk',
              score: 0.91,
              sourceFilename: 'real.txt',
              chunkIndex: 0,
              metadata: {},
            },
          ],
        },
      },
    })

    const result = await generateMerchantProductCopy({
      title: 'Jrun Air 14',
      category: 'laptop',
      sellingPoints: ['portable'],
      tone: 'professional',
      modelProvider: 'qwen',
      modelName: 'qwen-plus',
      knowledgeBaseId: 'kb-real',
    })

    expect(http.post).toHaveBeenCalledWith(
      '/product/ai/product-copy/generate',
      expect.objectContaining({ knowledgeBaseId: 'kb-real' }),
      expect.objectContaining({ timeout: expect.any(Number) }),
    )
    expect(result.response_source).toBe('rag')
    expect(result.embeddingProvider).toBe('mock-embedding')
    expect(result.usedChunks?.[0].knowledgeBaseId).toBe('kb-real')
  })
})
