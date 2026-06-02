import axios from 'axios'

import { fallbackMerchantProducts } from '@/data/fallbackProducts'
import { http } from '@/services/http'
import type {
  MerchantImageUploadResponse,
  MerchantProduct,
  MerchantProductCreatePayload,
  MerchantProductUpdatePayload,
} from '@/types/merchant'
import type { BackendResponse } from '@/types/productAi'

const placeholderImage = '/placeholders/products/default-product.svg'

function normalizeProduct(item: MerchantProduct): MerchantProduct {
  return {
    ...item,
    price: Number(item.price) || 0,
    coverUrl: item.coverUrl?.trim() ? item.coverUrl.trim() : placeholderImage,
    sellingPoints: Array.isArray(item.sellingPoints) ? item.sellingPoints.filter(Boolean) : [],
  }
}

export async function fetchMerchantProducts(): Promise<{ source: 'api' | 'fallback'; items: MerchantProduct[] }> {
  try {
    const response = await http.get<BackendResponse<{ items: MerchantProduct[] }>>('/product/merchant/products')
    const items = response.data?.data?.items

    if (Array.isArray(items) && items.length > 0) {
      return {
        source: 'api',
        items: items.map(normalizeProduct),
      }
    }
  } catch (error) {
    if (!axios.isAxiosError(error)) {
      throw error
    }
  }

  return {
    source: 'fallback',
    items: fallbackMerchantProducts.map((item) =>
      normalizeProduct({
        ...item,
        sellingPoints: [...item.sellingPoints],
      }),
    ),
  }
}

export async function fetchMerchantProductDetail(id: number): Promise<MerchantProduct> {
  const response = await http.get<BackendResponse<MerchantProduct>>(`/product/merchant/products/${id}`)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '商品详情接口返回异常')
  }
  return normalizeProduct(response.data.data)
}

export async function updateMerchantProduct(id: number, payload: MerchantProductUpdatePayload): Promise<MerchantProduct> {
  const response = await http.put<BackendResponse<MerchantProduct>>(`/product/merchant/products/${id}`, payload)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '商品更新失败')
  }
  return normalizeProduct(response.data.data)
}

export async function createMerchantProduct(payload: MerchantProductCreatePayload): Promise<MerchantProduct> {
  const response = await http.post<BackendResponse<MerchantProduct>>('/product/merchant/products', payload)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '商品创建失败')
  }
  return normalizeProduct(response.data.data)
}

export async function uploadMerchantProductImage(file: File): Promise<MerchantImageUploadResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<BackendResponse<MerchantImageUploadResponse>>(
    '/product/merchant/products/upload-image',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    },
  )
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(
      response.data.msg || '图片上传失败。若当前未配置 OSS，请先填写 .env.local 中的 JRUNMALL_OSS_* 变量，或继续手动填写图片 URL。',
    )
  }
  return response.data.data
}


