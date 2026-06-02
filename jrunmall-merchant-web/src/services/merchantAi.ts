import axios from 'axios'

import { fallbackModels } from '@/data/fallbackProducts'
import type { MerchantOption } from '@/types/merchant'
import type { BackendResponse, ProductAiGenerateInput, ProductAiResult } from '@/types/productAi'

import { http } from './http'
import { fetchKnowledgeBaseOptions } from './merchantKnowledgeBases'

const DEFAULT_AI_GENERATE_TIMEOUT_MS = 90_000

export class MerchantAiValidationError extends Error {
  fieldErrors: Record<string, string>

  constructor(message: string, fieldErrors: Record<string, string>) {
    super(message)
    this.name = 'MerchantAiValidationError'
    this.fieldErrors = fieldErrors
  }
}

export async function fetchAiModels(): Promise<MerchantOption[]> {
  try {
    const response = await http.get<BackendResponse<MerchantOption[]>>('/product/ai/models')
    if (Array.isArray(response.data?.data) && response.data.data.length > 0) {
      return response.data.data
    }
  } catch (error) {
    if (!axios.isAxiosError(error) && !(error instanceof Error)) {
      throw error
    }
  }

  return fallbackModels
}

export async function fetchKnowledgeBases(): Promise<MerchantOption[]> {
  try {
    return await fetchKnowledgeBaseOptions()
  } catch (error) {
    if (!axios.isAxiosError(error) && !(error instanceof Error)) {
      throw error
    }
  }

  return []
}

export async function generateMerchantProductCopy(
  payload: ProductAiGenerateInput,
): Promise<ProductAiResult> {
  let body: BackendResponse<ProductAiResult | Record<string, string>>

  try {
    const response = await http.post<BackendResponse<ProductAiResult | Record<string, string>>>(
      '/product/ai/product-copy/generate',
      payload,
      { timeout: resolveAiGenerateTimeoutMs() },
    )
    body = response.data
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.data) {
      body = error.response.data as BackendResponse<ProductAiResult | Record<string, string>>
    } else {
      throw error
    }
  }

  if (body.code === 10001) {
    throw new MerchantAiValidationError(body.msg || '参数校验失败', (body.data as Record<string, string>) || {})
  }

  if (body.code !== 0 || !body.data || typeof body.data !== 'object') {
    throw new Error(body.msg || '商品 AI 请求失败')
  }

  return body.data as ProductAiResult
}

function resolveAiGenerateTimeoutMs() {
  const configured = Number(import.meta.env.VITE_AI_GENERATE_TIMEOUT_MS)
  if (Number.isFinite(configured) && configured >= 10_000) {
    return configured
  }
  return DEFAULT_AI_GENERATE_TIMEOUT_MS
}

