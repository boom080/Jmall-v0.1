import axios from 'axios'

import { fallbackProducts } from '@/data/products'
import type {
  BackendResponse,
  CatalogProduct,
  ProductDetailResult,
  ProductListResult,
  UserCatalogApiDetailItem,
  UserCatalogApiPage,
} from '@/types/product'

import { http } from './http'
import { mapCatalogCard, mapCatalogDetail } from './catalogMapper'

function cloneFallbackProducts(): CatalogProduct[] {
  return fallbackProducts.map((product) => ({
    ...product,
    sellingPoints: [...product.sellingPoints],
    imageUrls: [...product.imageUrls],
    detailAttributes: [...product.detailAttributes],
  }))
}

function normalizeErrorMessage(error: unknown, fallbackMessage: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.msg || error.message
    return detail ? `${fallbackMessage} (${detail})` : fallbackMessage
  }
  if (error instanceof Error) {
    return error.message ? `${fallbackMessage} (${error.message})` : fallbackMessage
  }
  return fallbackMessage
}

export async function fetchCatalogProducts(params: Record<string, string | number> = {}): Promise<ProductListResult> {
  try {
    const response = await http.get<BackendResponse<UserCatalogApiPage>>('/product/user/catalog/products', {
      params: {
        page: 1,
        limit: 12,
        ...params,
      },
    })

    const body = response.data
    if (body.code !== 0 || !body.data || !Array.isArray(body.data.items)) {
      throw new Error(body.msg || '商品列表接口返回异常')
    }

    return {
      source: 'api',
      items: body.data.items.map(mapCatalogCard),
    }
  } catch (error) {
    return {
      source: 'fallback',
      items: cloneFallbackProducts(),
      errorMessage: normalizeErrorMessage(error, '商品列表接口暂时不可用，已回退到本地展示数据。'),
    }
  }
}

export async function fetchFeaturedProducts(limit = 4): Promise<ProductListResult> {
  const result = await fetchCatalogProducts({ page: 1, limit })
  return {
    ...result,
    items: result.items.slice(0, limit),
  }
}

export async function fetchCatalogProductById(productId: string): Promise<ProductDetailResult> {
  try {
    const response = await http.get<BackendResponse<UserCatalogApiDetailItem>>(`/product/user/catalog/products/${productId}`)
    const body = response.data

    if (body.code !== 0 || !body.data) {
      throw new Error(body.msg || '商品详情接口返回异常')
    }

    return {
      source: 'api',
      product: mapCatalogDetail(body.data),
    }
  } catch (error) {
    const fallbackProduct = await resolveFallbackProductDetail(productId)
    return {
      source: 'fallback',
      product: fallbackProduct,
      errorMessage: fallbackProduct ? undefined : normalizeErrorMessage(error, '商品详情接口暂时不可用，已回退到本地详情数据。'),
    }
  }
}

async function resolveFallbackProductDetail(productId: string): Promise<CatalogProduct | null> {
  const catalog = await fetchCatalogProducts({ page: 1, limit: 100 })
  const catalogProduct = catalog.items.find((item) => String(item.id) === String(productId))
  if (catalogProduct) {
    return {
      ...catalogProduct,
      detail: catalogProduct.detail || catalogProduct.summary || catalogProduct.subtitle,
      detailAttributes: [...catalogProduct.detailAttributes],
      imageUrls: [...catalogProduct.imageUrls],
      sellingPoints: [...catalogProduct.sellingPoints],
    }
  }

  return cloneFallbackProducts().find((item) => String(item.id) === String(productId)) || null
}


