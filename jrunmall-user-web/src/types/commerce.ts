export type CommerceSource = 'api' | 'fallback'
export type OrderStatus = 'CREATED' | 'PAID' | 'CANCELLED'
export type SeckillCode = 'ACCEPTED' | 'DUPLICATE_REQUEST' | 'SOLD_OUT' | 'NOT_STARTED' | 'ENDED' | 'ACTIVITY_NOT_FOUND' | 'INVALID_REQUEST' | 'INTERNAL_ERROR'

export interface BackendResponse<T> {
  code: number
  msg: string
  data: T
}

export interface UserCartApiItem {
  skuId: number
  title: string
  category: string
  price: number | string
  quantity: number
  coverUrl: string
  summary: string
  totalAmount: number | string
}

export interface UserCartApiResponse {
  userId: number
  displayName: string
  totalCount: number
  totalAmount: number | string
  items: UserCartApiItem[]
}

export interface CartItem {
  skuId: number
  title: string
  category: string
  price: number
  quantity: number
  coverUrl: string
  summary: string
  totalAmount: number
}

export interface CartSnapshot {
  source: CommerceSource
  userId: number
  displayName: string
  totalCount: number
  totalAmount: number
  items: CartItem[]
  errorMessage?: string
}

export interface UserOrderApiItem {
  skuId: number
  title: string
  category: string
  coverUrl: string
  summary: string
  price: number | string
  quantity: number
  lineAmount: number | string
}

export interface UserOrderApiResponse {
  orderId: number
  orderRef?: string
  orderSn: string
  userId: number
  username: string
  status: OrderStatus
  totalAmount: number | string
  totalQuantity: number
  note: string
  orderSource?: string
  bizToken?: string
  addressId?: number
  receiverName?: string
  receiverPhone?: string
  receiverAddress?: string
  createdTime: string
  paymentTime?: string
  items: UserOrderApiItem[]
}

export interface SeckillOrderApiResponse {
  orderId: number
  orderSn: string
  userId: number
  username: string
  skuId: number
  title: string
  quantity: number
  status: OrderStatus
  source: 'seckill'
  totalAmount: number | string
  createdAt: string
}

export interface OrderItem {
  skuId: number
  title: string
  category: string
  coverUrl: string
  summary: string
  price: number
  quantity: number
  lineAmount: number
}

export interface OrderSummary {
  orderId: number
  orderRef?: string
  orderSn: string
  userId: number
  username: string
  status: OrderStatus
  totalAmount: number
  totalQuantity: number
  note: string
  orderSource?: string
  bizToken?: string
  addressId?: number
  receiverName?: string
  receiverPhone?: string
  receiverAddress?: string
  createdTime: string
  paymentTime?: string
  items: OrderItem[]
}

export interface MerchantOrderSummary {
  orderId: number
  orderSn: string
  userId: number
  username: string
  status: OrderStatus
  totalAmount: number
  totalQuantity: number
  createdTime: string
  paymentTime?: string
}

export interface SeckillDeal {
  title: string
  category: string
  coverUrl: string
  summary: string
  price: number | string
  limitPerOrder: number
}

export interface SeckillSubmitRequest {
  quantity: number
  requestId?: string
}

export interface SeckillSubmitResponse {
  accepted: boolean
  code: SeckillCode
  message: string
  quantity: number
  orderId?: number
  orderRef?: string
  orderSn?: string
}


