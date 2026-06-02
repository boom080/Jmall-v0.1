export type ProductAiTone = 'professional' | 'marketing' | 'warm' | 'concise'

export interface ProductAiGenerateInput {
  title: string
  category: string
  sellingPoints: string[]
  tone: ProductAiTone
  modelProvider: string
  modelName: string
  knowledgeBaseId?: string
}

export interface ProductAiResult {
  generatedTitle: string
  highlights: string[]
  summary: string
  pendingMerchantConfirmations?: string[]
  provider: string
  mock: boolean
  success: boolean
  message: string
  response_source?: 'rag' | 'no_rag_fallback' | string
  usedChunks?: RagUsedChunk[]
  citations?: RagUsedChunk[]
  embeddingProvider?: string
}

export interface RagUsedChunk {
  chunkId: string
  documentId: string
  knowledgeBaseId: string
  content: string
  score: number
  sourceFilename: string
  chunkIndex: number
  metadata: Record<string, unknown>
}

export interface BackendResponse<T> {
  code: number
  msg: string
  data: T
}


