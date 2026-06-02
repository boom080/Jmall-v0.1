import type { MerchantOrderSummary } from '@/types/merchant'
import type { BackendResponse } from '@/types/productAi'

import { http } from './http'

export async function fetchMerchantOrders(): Promise<MerchantOrderSummary[]> {
  const response = await http.get<BackendResponse<MerchantOrderSummary[]>>('/product/merchant/orders')
  const items = response.data?.data

  if (!Array.isArray(items)) {
    throw new Error(response.data?.msg || '订单列表接口返回异常')
  }

  return items
}


