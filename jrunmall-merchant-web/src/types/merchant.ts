export interface MerchantProduct {
  id: number
  title: string
  category: string
  price: number
  sellingPoints: string[]
  coverUrl: string
  status: 'draft' | 'ready'
}

export interface MerchantProductUpdatePayload {
  title: string
  category: string
  price: number
  sellingPoints: string[]
  coverUrl: string
  status: 'draft' | 'ready'
}

export type MerchantProductCreatePayload = MerchantProductUpdatePayload

export interface MerchantImageUploadResponse {
  objectKey: string
  url: string
}

export interface MerchantOption {
  id: string
  label: string
  provider?: string
  description?: string
  documentCount?: number
  chunkCount?: number
  embeddingStatus?: string
  updatedAt?: string
}

export interface MerchantKnowledgeBase {
  id: string
  label: string
  description: string
  documentCount: number
  chunkCount: number
  embeddingStatus: string
  updatedAt: string
  source: string
}

export interface MerchantKnowledgeBaseDocument {
  id: string
  knowledgeBaseId: string
  title: string
  chunkCount: number
  embeddingStatus: string
  updatedAt: string
  contentPreview: string
}

export interface MerchantKnowledgeBaseCreatePayload {
  name: string
  description: string
}

export interface MerchantKnowledgeDocumentTextPayload {
  title: string
  content: string
}

export interface MerchantKnowledgeDocumentPdfPayload {
  title: string
  file: File
}

export interface MerchantKnowledgeBaseUploadTxtPayload {
  name: string
  description: string
  file: File
}

export interface MerchantKnowledgeBaseUploadTxtResponse {
  knowledgeBaseId: string
  name: string
  documentId: string
  chunkCount: number
  embeddingProvider: string
  status: string
}

export interface MerchantOrderSummary {
  orderId: number
  orderSn: string
  userId: number
  username: string
  status: 'CREATED' | 'PAID' | 'CANCELLED'
  totalAmount: number
  totalQuantity: number
  createdTime: string
  paymentTime?: string
}

export interface MerchantSeckillOrderSummary {
  orderId: number
  orderSn: string
  userId: number
  username?: string
  skuId?: number
  title: string
  quantity: number
  status: 'CREATED' | 'PAID' | 'CANCELLED'
  source: 'seckill'
  totalAmount: number
  createdAt: string
}


