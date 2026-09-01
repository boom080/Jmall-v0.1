import { beforeEach, describe, expect, it, vi } from 'vitest'

const { post } = vi.hoisted(() => ({ post: vi.fn() }))

vi.mock('@/services/http', () => ({
  default: { post },
}))

import {
  buildSelectedImageSource,
  aiImageApi,
  imageRiskLabel,
  imageSearchInputHint,
  normalizeAiDraftMeta,
  type ImageCandidate,
} from '@/services/aiImages'


const candidate: ImageCandidate = {
  candidate_id: 'img-1',
  title: '轻量保温杯',
  thumbnail_url: 'https://thumbs.example.com/cup.jpg',
  original_url: 'https://images.example.com/cup.jpg',
  source_page_url: 'https://publisher.example.com/cup',
  source_name: 'Publisher',
  author: 'Publisher',
  width: 1200,
  height: 1200,
  risk_flags: ['license_unverified', 'possible_watermark'],
  risk_reasons: ['图片使用权未经核验', '可能带水印'],
}


describe('Image Scout selection evidence', () => {
  beforeEach(() => post.mockReset())

  it('sends confirmed product facts to the free Image Scout proxy', async () => {
    post.mockResolvedValue({ status: 'no_results', candidates: [] })
    const productInfo = {
      title: '轻量保温杯',
      category: '家居日用',
      targetAudience: '学生和上班族',
    }

    await aiImageApi.candidates(productInfo)

    expect(post).toHaveBeenCalledOnce()
    expect(post).toHaveBeenCalledWith('/ai/images/candidates', { productInfo })
  })

  it('records source, risks, provider, and explicit confirmation time', () => {
    const selected = buildSelectedImageSource(
      candidate,
      'serpapi_google_images',
      '2026-08-26T08:00:00.000Z',
    )

    expect(selected).toMatchObject({
      type: 'search',
      candidate_id: 'img-1',
      original_url: candidate.original_url,
      source_page_url: candidate.source_page_url,
      provider: 'serpapi_google_images',
      user_confirmed: true,
      confirmed_at: '2026-08-26T08:00:00.000Z',
    })
    expect(selected.risk_flags).toEqual(['license_unverified', 'possible_watermark'])
  })

  it('uses stable Chinese labels for known risk flags', () => {
    expect(imageRiskLabel('license_unverified')).toBe('使用权未核验')
    expect(imageRiskLabel('visual_risk_unverified')).toBe('请人工检查水印/品牌')
    expect(imageRiskLabel('possible_watermark')).toBe('可能含水印')
    expect(imageRiskLabel('custom-risk')).toBe('custom-risk')
  })

  it('normalizes invalid or null draft metadata to a safe object', () => {
    expect(normalizeAiDraftMeta(null)).toEqual({})
    expect(normalizeAiDraftMeta('null')).toEqual({})
    expect(normalizeAiDraftMeta('[1, 2]')).toEqual({})
    expect(normalizeAiDraftMeta('{broken')).toEqual({})
    expect(normalizeAiDraftMeta('{"selected_image_source":{"user_confirmed":true}}'))
      .toEqual({ selected_image_source: { user_confirmed: true } })
  })

  it('blocks an empty image search before calling the backend', () => {
    expect(imageSearchInputHint({ title: '', category: '' }))
      .toBe('请先填写商品名称和品类，再让 Image Scout 判断信息是否完整')
    expect(imageSearchInputHint({ title: '轻量保温杯', category: '家居日用' })).toBe('')
  })
})
