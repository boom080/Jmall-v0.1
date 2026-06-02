export interface CatalogProduct {
  id: number
  title: string
  category: string
  subtitle: string
  sellingPoints: string[]
  price: number
  coverUrl: string
  imageUrls: string[]
  summary: string
  detail: string
  detailAttributes: string[]
}

export interface ProductListResult {
  source: 'api' | 'fallback'
  items: CatalogProduct[]
  errorMessage?: string
}

export interface ProductDetailResult {
  source: 'api' | 'fallback'
  product: CatalogProduct | null
  errorMessage?: string
}

export interface UserCatalogApiCardItem {
  id: number
  title: string
  category: string
  subtitle: string
  sellingPoints: string[]
  price: number | string
  coverUrl: string
  summary: string
}

export interface UserCatalogApiDetailItem extends UserCatalogApiCardItem {
  detail: string
  imageUrls: string[]
  detailAttributes: string[]
}

export interface UserCatalogApiPage {
  items: UserCatalogApiCardItem[]
  totalCount: number
  pageSize: number
  currentPage: number
  totalPage: number
}

export interface BackendResponse<T> {
  code: number
  msg: string
  data: T
}


