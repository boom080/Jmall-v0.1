import http from './http'

export type ImageRiskFlag =
  | 'license_unverified'
  | 'visual_risk_unverified'
  | 'possible_watermark'
  | 'possible_competitor_brand'
  | 'low_resolution'
  | 'resolution_unknown'
  | 'insecure_http'

export interface ImageCandidate {
  candidate_id: string
  title: string
  thumbnail_url: string
  original_url: string
  source_page_url: string
  source_name: string
  author: string
  width?: number | null
  height?: number | null
  risk_flags: ImageRiskFlag[] | string[]
  risk_reasons: string[]
}

export interface ImageCandidatesResponse {
  status: 'ready' | 'needs_input' | 'no_results' | 'provider_unavailable' | 'provider_error'
  query: string
  provider: string
  candidates: ImageCandidate[]
  input_assessment?: Record<string, unknown>
  message: string
  disclaimer: string
}

export interface SelectedImageSource {
  type: 'search'
  candidate_id: string
  original_url: string
  source_page_url: string
  source_name: string
  author: string
  provider: string
  risk_flags: string[]
  risk_reasons: string[]
  user_confirmed: true
  confirmed_at: string
}

export const aiImageApi = {
  candidates(productInfo: Record<string, unknown>): Promise<ImageCandidatesResponse> {
    return http.post('/ai/images/candidates', { productInfo })
  },
}

export function buildSelectedImageSource(
  candidate: ImageCandidate,
  provider: string,
  confirmedAt = new Date().toISOString(),
): SelectedImageSource {
  return {
    type: 'search',
    candidate_id: candidate.candidate_id,
    original_url: candidate.original_url,
    source_page_url: candidate.source_page_url,
    source_name: candidate.source_name,
    author: candidate.author,
    provider,
    risk_flags: [...candidate.risk_flags],
    risk_reasons: [...candidate.risk_reasons],
    user_confirmed: true,
    confirmed_at: confirmedAt,
  }
}

export function imageRiskLabel(flag: string): string {
  const labels: Record<string, string> = {
    license_unverified: '使用权未核验',
    visual_risk_unverified: '请人工检查水印/品牌',
    possible_watermark: '可能含水印',
    possible_competitor_brand: '可能含第三方品牌',
    low_resolution: '清晰度偏低',
    resolution_unknown: '清晰度未知',
    insecure_http: '非 HTTPS 链接',
  }
  return labels[flag] || flag
}

export function normalizeAiDraftMeta(value: unknown): Record<string, unknown> {
  try {
    const parsed = typeof value === 'string' ? JSON.parse(value) : value
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return {}
    return { ...(parsed as Record<string, unknown>) }
  } catch {
    return {}
  }
}

export function imageSearchInputHint(productInfo: Record<string, unknown>): string {
  if (!String(productInfo.title || '').trim() || !String(productInfo.category || '').trim()) {
    return '请先填写商品名称和品类，再让 Image Scout 判断信息是否完整'
  }
  return ''
}
