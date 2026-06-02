import type {
  MerchantKnowledgeBase,
  MerchantKnowledgeBaseCreatePayload,
  MerchantKnowledgeBaseDocument,
  MerchantKnowledgeBaseUploadTxtPayload,
  MerchantKnowledgeBaseUploadTxtResponse,
  MerchantKnowledgeDocumentPdfPayload,
  MerchantKnowledgeDocumentTextPayload,
  MerchantOption,
} from '@/types/merchant'
import type { BackendResponse } from '@/types/productAi'

import { http } from './http'

function requireResponseData<T>(body: BackendResponse<T> | undefined, fallbackMessage: string): T {
  if (!body || body.code !== 0 || body.data === undefined || body.data === null) {
    throw new Error(body?.msg || fallbackMessage)
  }
  return body.data
}

function normalizeKnowledgeBase(item: MerchantKnowledgeBase): MerchantKnowledgeBase {
  return {
    ...item,
    description: item.description || '',
    documentCount: Number(item.documentCount || 0),
    chunkCount: Number(item.chunkCount || 0),
    embeddingStatus: item.embeddingStatus || 'empty',
    updatedAt: item.updatedAt || '',
    source: item.source || 'api',
  }
}

function normalizeDocument(item: MerchantKnowledgeBaseDocument): MerchantKnowledgeBaseDocument {
  return {
    ...item,
    chunkCount: Number(item.chunkCount || 0),
    embeddingStatus: item.embeddingStatus || 'pending',
    updatedAt: item.updatedAt || '',
    contentPreview: item.contentPreview || '',
  }
}

export async function fetchMerchantKnowledgeBases(): Promise<MerchantKnowledgeBase[]> {
  const response = await http.get<BackendResponse<MerchantKnowledgeBase[]>>('/product/merchant/knowledge-bases')
  if (response.data.code !== 0) {
    throw new Error(response.data.msg || '知识库列表加载失败')
  }
  return Array.isArray(response.data.data) ? response.data.data.map(normalizeKnowledgeBase) : []
}

export async function createMerchantKnowledgeBase(
  payload: MerchantKnowledgeBaseCreatePayload,
): Promise<MerchantKnowledgeBase> {
  const response = await http.post<BackendResponse<MerchantKnowledgeBase>>(
    '/product/merchant/knowledge-bases',
    payload,
  )
  return normalizeKnowledgeBase(requireResponseData(response.data, '知识库创建失败'))
}

export async function fetchKnowledgeBaseDocuments(
  knowledgeBaseId: string,
): Promise<MerchantKnowledgeBaseDocument[]> {
  const response = await http.get<BackendResponse<MerchantKnowledgeBaseDocument[]>>(
    `/product/merchant/knowledge-bases/${knowledgeBaseId}/documents`,
  )
  if (response.data.code !== 0) {
    throw new Error(response.data.msg || '知识库文档加载失败')
  }
  return Array.isArray(response.data.data) ? response.data.data.map(normalizeDocument) : []
}

export async function importKnowledgeBaseTextDocument(
  knowledgeBaseId: string,
  payload: MerchantKnowledgeDocumentTextPayload,
): Promise<MerchantKnowledgeBaseDocument> {
  const response = await http.post<BackendResponse<MerchantKnowledgeBaseDocument>>(
    `/product/merchant/knowledge-bases/${knowledgeBaseId}/documents/text`,
    payload,
  )
  return normalizeDocument(requireResponseData(response.data, '文本导入失败'))
}

export async function importKnowledgeBasePdfDocument(
  knowledgeBaseId: string,
  payload: MerchantKnowledgeDocumentPdfPayload,
): Promise<MerchantKnowledgeBaseDocument> {
  const formData = new FormData()
  formData.append('title', payload.title)
  formData.append('file', payload.file)
  const response = await http.post<BackendResponse<MerchantKnowledgeBaseDocument>>(
    `/product/merchant/knowledge-bases/${knowledgeBaseId}/documents/pdf`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  )
  return normalizeDocument(requireResponseData(response.data, 'PDF 导入失败'))
}

export async function uploadTxtCreateKnowledgeBase(
  payload: MerchantKnowledgeBaseUploadTxtPayload,
): Promise<MerchantKnowledgeBaseUploadTxtResponse> {
  const formData = new FormData()
  formData.append('name', payload.name)
  formData.append('description', payload.description)
  formData.append('file', payload.file)
  const response = await http.post<BackendResponse<MerchantKnowledgeBaseUploadTxtResponse>>(
    '/product/ai/knowledge-bases/upload-txt',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  )
  return requireResponseData(response.data, 'txt 上传创建知识库失败')
}

export async function fetchKnowledgeBaseOptions(): Promise<MerchantOption[]> {
  const knowledgeBases = await fetchMerchantKnowledgeBases()
  return knowledgeBases.map((item) => ({
    id: item.id,
    label: item.label,
    description: item.description,
    documentCount: item.documentCount,
    chunkCount: item.chunkCount,
    embeddingStatus: item.embeddingStatus,
    updatedAt: item.updatedAt,
  }))
}


