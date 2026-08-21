import http from './http'
import type { Store } from '@/types'

export const storeApi = {
  getMyStore(): Promise<Store> {
    return http.get('/stores/mine')
  },
  getMyStats(): Promise<{ storeId: number; productCount: number; totalSales: number; totalOrders: number }> {
    return http.get('/stores/mine/stats')
  },
  getById(id: number): Promise<Store> {
    return http.get(`/stores/${id}`)
  },
  getStats(id: number): Promise<{ storeId: number; productCount: number; totalSales: number; totalOrders: number }> {
    return http.get(`/stores/${id}/stats`)
  },
  create(data: { name: string; category: string; description: string }): Promise<Store> {
    return http.post('/stores', data)
  },
  update(id: number, data: { name: string; category: string; description: string; decorationConfig?: string }): Promise<Store> {
    return http.put(`/stores/${id}`, data)
  },
}
