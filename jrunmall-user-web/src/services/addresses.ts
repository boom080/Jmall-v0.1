import type { UserAddress } from '@/types/auth'
import type { BackendResponse } from '@/types/commerce'

import { http } from './http'

export async function fetchAddresses(): Promise<UserAddress[]> {
  const response = await http.get<BackendResponse<UserAddress[]>>('/user/addresses')
  if (response.data.code !== 0 || !Array.isArray(response.data.data)) {
    throw new Error(response.data.msg || '获取地址列表失败')
  }
  return response.data.data
}

export async function createAddress(payload: UserAddress): Promise<UserAddress> {
  const response = await http.post<BackendResponse<UserAddress>>('/user/addresses', payload)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '新增地址失败')
  }
  return response.data.data
}

export async function updateAddress(addressId: number, payload: UserAddress): Promise<UserAddress> {
  const response = await http.put<BackendResponse<UserAddress>>(`/user/addresses/${addressId}`, payload)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '更新地址失败')
  }
  return response.data.data
}

export async function deleteAddress(addressId: number) {
  const response = await http.delete<BackendResponse<unknown>>(`/user/addresses/${addressId}`)
  if (response.data.code !== 0) {
    throw new Error(response.data.msg || '删除地址失败')
  }
}


