import type { BackendResponse } from '@/types/commerce'
import type { CurrentUserProfile, LoginPayload, LoginResponse, RegisterPayload } from '@/types/auth'

import { http } from './http'

export async function registerUser(payload: RegisterPayload) {
  const response = await http.post<BackendResponse<unknown>>('/user/auth/register', payload)
  if (response.data.code !== 0) {
    throw new Error(response.data.msg || '注册失败')
  }
}

export async function loginUser(payload: LoginPayload): Promise<LoginResponse> {
  const response = await http.post<BackendResponse<LoginResponse>>('/user/auth/login', payload)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '登录失败')
  }
  return response.data.data
}

export async function fetchCurrentUser(): Promise<CurrentUserProfile> {
  const response = await http.get<BackendResponse<CurrentUserProfile>>('/user/auth/me')
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '获取当前用户失败')
  }
  return response.data.data
}

export async function logoutUser() {
  await http.post('/user/auth/logout')
}


