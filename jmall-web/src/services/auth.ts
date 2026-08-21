import http from './http'
import type { LoginPayload, RegisterPayload, CurrentUser } from '@/types'

interface LoginResponse {
  token: string
  user: CurrentUser
}

export const authApi = {
  login(payload: LoginPayload): Promise<LoginResponse> {
    return http.post('/auth/login', payload)
  },
  register(payload: RegisterPayload): Promise<void> {
    return http.post('/auth/register', payload)
  },
  me(): Promise<CurrentUser> {
    return http.get('/auth/me')
  },
  logout(): Promise<void> {
    return http.post('/auth/logout')
  },
}
