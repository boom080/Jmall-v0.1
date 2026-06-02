import type { CatalogProduct, UserCatalogApiCardItem, UserCatalogApiDetailItem } from '@/types/product'

const placeholder = '/placeholders/products/default-product.svg'

export function resolveProductCover(coverUrl?: string | null, imageUrls?: string[]): string {
  const normalizedCover = typeof coverUrl === 'string' ? coverUrl.trim() : ''
  if (normalizedCover) {
    return normalizedCover
  }

  const matchedImage = (imageUrls || []).find((item) => typeof item === 'string' && item.trim())
  return matchedImage?.trim() || placeholder
}

function normalizePoints(points?: string[]): string[] {
  if (!Array.isArray(points)) {
    return []
  }
  return points.map((item) => String(item || '').trim()).filter(Boolean)
}

function normalizePrice(value: string | number): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function mapCatalogCard(item: UserCatalogApiCardItem): CatalogProduct {
  return {
    id: Number(item.id),
    title: item.title || '未命名商品',
    category: item.category || '未分类',
    subtitle: item.subtitle || item.summary || '真实商品列表',
    sellingPoints: normalizePoints(item.sellingPoints),
    price: normalizePrice(item.price),
    coverUrl: resolveProductCover(item.coverUrl),
    imageUrls: [resolveProductCover(item.coverUrl)],
    summary: item.summary || item.subtitle || '真实商品接口聚合结果',
    detail: item.summary || item.subtitle || '暂无更多商品详情',
    detailAttributes: [],
  }
}

export function mapCatalogDetail(item: UserCatalogApiDetailItem): CatalogProduct {
  const imageUrls = normalizePoints(item.imageUrls)
  const coverUrl = resolveProductCover(item.coverUrl, imageUrls)

  return {
    id: Number(item.id),
    title: item.title || '未命名商品',
    category: item.category || '未分类',
    subtitle: item.subtitle || item.summary || '真实商品详情',
    sellingPoints: normalizePoints(item.sellingPoints),
    price: normalizePrice(item.price),
    coverUrl,
    imageUrls: imageUrls.length ? imageUrls : [coverUrl],
    summary: item.summary || item.subtitle || '真实商品详情聚合结果',
    detail: item.detail || item.summary || '暂无更多商品详情',
    detailAttributes: normalizePoints(item.detailAttributes),
  }
}


