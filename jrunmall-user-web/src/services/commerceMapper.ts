import type {
  CartItem,
  CartSnapshot,
  MerchantOrderSummary,
  OrderItem,
  OrderSummary,
  SeckillOrderApiResponse,
  UserCartApiItem,
  UserCartApiResponse,
  UserOrderApiItem,
  UserOrderApiResponse,
} from '@/types/commerce'

const placeholderImage = '/placeholders/products/default-product.svg'

function toNumber(value: number | string | undefined): number {
  if (typeof value === 'number') {
    return value
  }
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function resolveProductImage(url?: string): string {
  return url && url.trim() ? url.trim() : placeholderImage
}

export function mapCartItem(item: UserCartApiItem): CartItem {
  return {
    skuId: Number(item.skuId),
    title: item.title || '未命名商品',
    category: item.category || '未分类',
    price: toNumber(item.price),
    quantity: Number(item.quantity) || 0,
    coverUrl: resolveProductImage(item.coverUrl),
    summary: item.summary || '暂无商品摘要',
    totalAmount: toNumber(item.totalAmount),
  }
}

export function mapCartSnapshot(response: UserCartApiResponse): CartSnapshot {
  return {
    source: 'api',
    userId: Number(response.userId),
    displayName: response.displayName || 'Jrunmall User',
    totalCount: Number(response.totalCount) || 0,
    totalAmount: toNumber(response.totalAmount),
    items: Array.isArray(response.items) ? response.items.map(mapCartItem) : [],
  }
}

export function mapOrderItem(item: UserOrderApiItem): OrderItem {
  return {
    skuId: Number(item.skuId),
    title: item.title || '未命名商品',
    category: item.category || '未分类',
    coverUrl: resolveProductImage(item.coverUrl),
    summary: item.summary || '暂无商品摘要',
    price: toNumber(item.price),
    quantity: Number(item.quantity) || 0,
    lineAmount: toNumber(item.lineAmount),
  }
}

export function mapOrder(response: UserOrderApiResponse): OrderSummary {
  return {
    orderId: Number(response.orderId),
    orderRef: response.orderRef || String(response.orderId),
    orderSn: response.orderSn,
    userId: Number(response.userId),
    username: response.username || 'jrunmall-user',
    status: response.status,
    totalAmount: toNumber(response.totalAmount),
    totalQuantity: Number(response.totalQuantity) || 0,
    note: response.note || '',
    orderSource: response.orderSource || 'normal',
    bizToken: response.bizToken || '',
    addressId: response.addressId ? Number(response.addressId) : undefined,
    receiverName: response.receiverName || '',
    receiverPhone: response.receiverPhone || '',
    receiverAddress: response.receiverAddress || '',
    createdTime: response.createdTime || '',
    paymentTime: response.paymentTime || '',
    items: Array.isArray(response.items) ? response.items.map(mapOrderItem) : [],
  }
}

export function mapSeckillOrder(response: SeckillOrderApiResponse): OrderSummary {
  const item: OrderItem = {
    skuId: Number(response.skuId),
    title: response.title || '未命名商品',
    category: '秒杀专区',
    coverUrl: resolveProductImage(''),
    summary: '来自 Go 秒杀 + Redis Streams + jrunmall-order 的秒杀订单',
    price: toNumber(response.totalAmount),
    quantity: Number(response.quantity) || 0,
    lineAmount: toNumber(response.totalAmount),
  }

  return {
    orderId: Number(response.orderId),
    orderRef: `seckill-${response.orderId}`,
    orderSn: response.orderSn,
    userId: Number(response.userId),
    username: response.username || `user-${response.userId}`,
    status: response.status,
    totalAmount: toNumber(response.totalAmount),
    totalQuantity: Number(response.quantity) || 0,
    note: '秒杀订单',
    orderSource: response.source || 'seckill',
    bizToken: '',
    createdTime: response.createdAt || '',
    paymentTime: '',
    items: [item],
  }
}

export function mapMerchantOrder(response: UserOrderApiResponse | MerchantOrderSummary): MerchantOrderSummary {
  return {
    orderId: Number(response.orderId),
    orderSn: response.orderSn,
    userId: Number(response.userId),
    username: response.username || 'jrunmall-user',
    status: response.status,
    totalAmount: toNumber(response.totalAmount),
    totalQuantity: Number(response.totalQuantity) || 0,
    createdTime: response.createdTime || '',
    paymentTime: response.paymentTime || '',
  }
}


