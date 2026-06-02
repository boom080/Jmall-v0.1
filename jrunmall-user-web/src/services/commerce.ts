import axios from 'axios'

import type {
  BackendResponse,
  CartSnapshot,
  MerchantOrderSummary,
  OrderSummary,
  UserCartApiResponse,
  UserOrderApiResponse,
} from '@/types/commerce'

import { http } from './http'
import { mapCartSnapshot, mapMerchantOrder, mapOrder } from './commerceMapper'

function normalizeErrorMessage(error: unknown, fallbackMessage: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.msg || error.message
    if (String(detail || '').includes('请先登录')) {
      return '请先登录后查看购物车'
    }
    return detail ? `${fallbackMessage}（${detail}）` : fallbackMessage
  }
  if (error instanceof Error) {
    if (error.message.includes('请先登录')) {
      return '请先登录后查看购物车'
    }
    return error.message ? `${fallbackMessage}（${error.message}）` : fallbackMessage
  }
  return fallbackMessage
}

export async function fetchCartItems(): Promise<CartSnapshot> {
  try {
    const response = await http.get<BackendResponse<UserCartApiResponse>>('/product/user/cart/items')
    if (response.data.code !== 0 || !response.data.data) {
      throw new Error(response.data.msg || '购物车接口返回异常')
    }
    return mapCartSnapshot(response.data.data)
  } catch (error) {
    return {
      source: 'fallback',
      userId: 0,
      displayName: '',
      totalCount: 0,
      totalAmount: 0,
      items: [],
      errorMessage: normalizeErrorMessage(error, '购物车接口暂时不可用'),
    }
  }
}

export async function addCartItem(skuId: number, quantity = 1): Promise<CartSnapshot> {
  const response = await http.post<BackendResponse<UserCartApiResponse>>('/product/user/cart/items', { skuId, quantity })
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '加入购物车失败')
  }
  return mapCartSnapshot(response.data.data)
}

export async function updateCartItem(skuId: number, quantity: number): Promise<CartSnapshot> {
  const response = await http.put<BackendResponse<UserCartApiResponse>>(`/product/user/cart/items/${skuId}`, { quantity })
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '更新购物车失败')
  }
  return mapCartSnapshot(response.data.data)
}

export async function removeCartItem(skuId: number): Promise<CartSnapshot> {
  const response = await http.delete<BackendResponse<UserCartApiResponse>>(`/product/user/cart/items/${skuId}`)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '删除购物车项失败')
  }
  return mapCartSnapshot(response.data.data)
}

export async function createOrder(addressId: number, note = ''): Promise<OrderSummary> {
  const response = await http.post<BackendResponse<UserOrderApiResponse>>('/product/user/orders', { addressId, note })
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '创建订单失败')
  }
  return mapOrder(response.data.data)
}

export async function confirmOrderAddress(orderId: number, addressId: number, note = ''): Promise<OrderSummary> {
  const response = await http.post<BackendResponse<UserOrderApiResponse>>(`/product/user/orders/${orderId}/address`, { addressId, note })
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '确认收货地址失败')
  }
  return mapOrder(response.data.data)
}

export async function fetchOrders(): Promise<OrderSummary[]> {
  const response = await http.get<BackendResponse<UserOrderApiResponse[]>>('/product/user/orders/all')
  if (response.data.code !== 0 || !Array.isArray(response.data.data)) {
    throw new Error(response.data.msg || '统一订单接口返回异常')
  }
  return response.data.data.map(mapOrder)
}

export async function fetchOrderById(orderId: string | number): Promise<OrderSummary> {
  const orderRef = String(orderId)
  const response = await http.get<BackendResponse<UserOrderApiResponse>>(`/product/user/orders/all/${orderRef}`)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '订单详情接口返回异常')
  }
  return mapOrder(response.data.data)
}

export async function payOrder(orderId: string | number): Promise<OrderSummary> {
  const response = await http.post<BackendResponse<UserOrderApiResponse>>(`/product/user/orders/${orderId}/pay`)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '模拟支付失败')
  }
  return mapOrder(response.data.data)
}

export async function fetchMerchantOrders(): Promise<MerchantOrderSummary[]> {
  const response = await http.get<BackendResponse<MerchantOrderSummary[]>>('/product/merchant/orders')
  if (response.data.code !== 0 || !Array.isArray(response.data.data)) {
    throw new Error(response.data.msg || '商家订单接口返回异常')
  }
  return response.data.data.map(mapMerchantOrder)
}


