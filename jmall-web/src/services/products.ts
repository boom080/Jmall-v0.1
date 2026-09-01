import http from './http'
import type { Product, PlatformStyle, CartItem, Order, PublishCheckResult } from '@/types'

export const productApi = {
  list(params: { category?: string; style?: PlatformStyle; status?: string; keyword?: string; page?: number; size?: number } = {}) {
    return http.get('/products', { params })
  },
  get(id: number, trackView = true): Promise<Product> {
    return http.get(`/products/${id}`, { params: { trackView } })
  },
  create(product: Partial<Product>): Promise<Product> {
    return http.post('/products', product)
  },
  update(id: number, product: Partial<Product>): Promise<Product> {
    return http.put(`/products/${id}`, product)
  },
  publishCheck(id: number): Promise<PublishCheckResult> {
    return http.post(`/products/${id}/publish-check`)
  },
  publish(id: number): Promise<Product> {
    return http.post(`/products/${id}/publish`)
  },
  unpublish(id: number): Promise<Product> {
    return http.post(`/products/${id}/unpublish`)
  },
  getMyProducts(page = 1, size = 20): Promise<{ records: Product[]; total: number; current: number; size: number }> {
    return http.get('/products/mine', { params: { page, size } })
  },
  purchase(productId: number): Promise<{ amount: number; transactionId: number }> {
    return http.post('/transactions', { productId })
  },
}

export const cartApi = {
  list(): Promise<CartItem[]> {
    return http.get('/cart')
  },
  add(productId: number, quantity = 1): Promise<any> {
    return http.post('/cart', { productId, quantity })
  },
  updateQuantity(cartItemId: number, quantity: number): Promise<any> {
    return http.put(`/cart/${cartItemId}/quantity`, { quantity })
  },
  remove(cartItemId: number): Promise<any> {
    return http.delete(`/cart/${cartItemId}`)
  },
  clear(): Promise<any> {
    return http.delete('/cart/clear')
  },
}

export const orderApi = {
  checkout(): Promise<{ orders: any[]; totalOrders: number }> {
    return http.post('/orders/checkout')
  },
  list(): Promise<Order[]> {
    return http.get('/orders')
  },
}
