export interface CurrentUserProfile {
  userId: number
  username: string
  displayName: string
}

export interface LoginPayload {
  loginacct: string
  password: string
}

export interface RegisterPayload {
  userName: string
  phone: string
  password: string
}

export interface LoginResponse {
  token: string
  user: CurrentUserProfile
}

export interface UserAddress {
  id?: number
  memberId?: number
  name: string
  phone: string
  province?: string
  city?: string
  region?: string
  detailAddress: string
  defaultStatus?: number
}


