import type { MerchantSeckillOrderSummary } from '@/types/merchant'
import type { BackendResponse } from '@/types/productAi'

import { orderHttp } from './orderHttp'

export async function fetchMerchantSeckillOrders(): Promise<MerchantSeckillOrderSummary[]> {
  const response = await orderHttp.get<BackendResponse<MerchantSeckillOrderSummary[]>>('/order/merchant/seckill-orders')
  const items = response.data?.data

  if (!Array.isArray(items)) {
    throw new Error(response.data?.msg || '秒杀订单列表接口返回异常')
  }

  return items
}


