import type { BackendResponse, SeckillDeal, SeckillSubmitRequest, SeckillSubmitResponse } from '@/types/commerce'

import { http } from './http'

export async function fetchCurrentSeckillDeal(): Promise<SeckillDeal> {
  const response = await http.get<BackendResponse<SeckillDeal>>('/product/user/seckill/current')
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '秒杀商品加载失败')
  }
  return response.data.data
}

export async function submitSeckill(request: SeckillSubmitRequest): Promise<SeckillSubmitResponse> {
  const response = await http.post<BackendResponse<SeckillSubmitResponse>>('/product/user/seckill/submit', request)
  if (response.data.code !== 0 || !response.data.data) {
    throw new Error(response.data.msg || '秒杀请求提交失败')
  }
  return response.data.data
}


