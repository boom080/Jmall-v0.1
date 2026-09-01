import { describe, expect, it } from 'vitest'
import {
  buildPlatformDraftPayload,
  extractPlatformSkillMetadata,
  filterSinglePlatformResult,
  isEditablePlatformContent,
  markEditablePlatformContent,
  mergePlatformDraftMeta,
  normalizePlatformDraft,
} from '@/utils/platformDraft'

describe('platform draft contract', () => {
  it('filters a legacy five-platform result to the requested target and keeps title punctuation', () => {
    const result = filterSinglePlatformResult({
      style_adaptation: {
        target_style: 'jd',
        previews: {
          taobao: { adapted_title: '淘宝旧稿', adapted_selling_points: ['旧'] },
          jd: {
            adapted_title: '35厘米，米白色托特包',
            adapted_selling_points: ['参数清晰'],
            adapted_detail: '【规格与细节】宽35厘米，高30厘米。',
            visual_params: { density: 'compact' },
            style_notes: '参数导向',
          },
          pinduoduo: { adapted_title: '拼多多旧稿' },
          suning: { adapted_title: '苏宁旧稿' },
          xiaohongshu: { adapted_title: '小红书旧稿' },
        },
      },
    }, 'jd')

    expect(result.target_style).toBe('jd')
    expect(Object.keys(result.style_adaptation.previews || {})).toEqual(['jd'])
    expect(result.style_adaptation.adapted_title).toBe('35厘米，米白色托特包')
    expect(result.draft.titles).toEqual(['35厘米，米白色托特包'])
    expect(result.style_adaptation.visual_params).toEqual({ density: 'compact' })
    expect(result.style_adaptation.style_notes).toBe('参数导向')
  })

  it('also filters a legacy top-level platform map before persistence', () => {
    const result = filterSinglePlatformResult({
      taobao: { adapted_title: '淘宝稿' },
      jd: { adapted_title: '京东稿' },
      pinduoduo: { adapted_title: '拼多多稿' },
      suning: { adapted_title: '苏宁稿' },
      xiaohongshu: { adapted_title: '小红书稿' },
    }, 'jd')

    expect(result.style_adaptation.jd).toBeUndefined()
    expect(result.style_adaptation.taobao).toBeUndefined()
    expect(Object.keys(result.style_adaptation.previews || {})).toEqual(['jd'])
    expect(result.draft.titles).toEqual(['京东稿'])
  })

  it('treats the unified draft as authoritative, including explicitly empty optional copy', () => {
    const draft = normalizePlatformDraft({
      adapted_title: '旧标题',
      subtitle: '旧副标题',
      promotion_copy: '旧推广语',
      short_video_script: '旧视频',
      draft: {
        titles: ['新标题'],
        selling_points: ['新卖点，保留逗号'],
        detail_copy: '新详情',
        subtitle: '',
        promotion_copy: '',
        short_video_script: '',
      },
    })

    expect(draft.titles).toEqual(['新标题'])
    expect(draft.selling_points).toEqual(['新卖点，保留逗号'])
    expect(draft.detail_copy).toBe('新详情')
    expect(draft.subtitle).toBe('')
    expect(draft.promotion_copy).toBe('')
    expect(draft.short_video_script).toBe('')
  })

  it('uses draft fields over conflicting legacy adapted fields', () => {
    const result = filterSinglePlatformResult({
      style_adaptation: {
        target_style: 'taobao',
        adapted_title: '旧适配标题',
        adapted_detail: '旧适配详情',
        draft: {
          titles: ['新权威标题'],
          selling_points: ['新权威卖点'],
          detail_copy: '新权威详情',
        },
      },
    }, 'taobao')

    expect(result.style_adaptation.adapted_title).toBe('新权威标题')
    expect(result.style_adaptation.adapted_detail).toBe('新权威详情')
    expect(result.draft.titles).toEqual(['新权威标题'])
    expect(result.draft.detail_copy).toBe('新权威详情')
  })

  it('keeps the independent Skill detail structure in the unified draft', () => {
    const result = filterSinglePlatformResult({
      style_adaptation: {
        target_style: 'pinduoduo',
        draft: {
          titles: ['平台标题'],
          selling_points: ['平台卖点'],
          detail_copy: '【商品信息】\n真实信息\n【规格参数】\n宽35厘米，高30厘米。\n【购买前核对】\n请商家确认批次。',
        },
      },
    }, 'pinduoduo')

    expect(result.draft.detail_copy).toContain('【商品信息】')
    expect(result.draft.detail_copy).toContain('【规格参数】')
    expect(result.draft.detail_copy).toContain('宽35厘米，高30厘米。')
  })

  it('extracts Skill provenance from generation metadata without inventing old versions', () => {
    expect(extractPlatformSkillMetadata({
      style_adaptation: { target_style: 'taobao', platform_skill_id: 'taobao-copy' },
      generation_metadata: { platform_skill_version: '2026.08.30' },
    })).toEqual({
      target_style: 'taobao',
      platform_skill_id: 'taobao-copy',
      platform_skill_version: '2026.08.30',
      fallback: false,
    })
    expect(extractPlatformSkillMetadata({ style_adaptation: { target_style: 'jd' } })).toEqual({
      target_style: 'jd',
      platform_skill_id: null,
      platform_skill_version: null,
      fallback: false,
    })
  })

  it('round-trips one platform payload and preserves existing metadata', () => {
    const payload = buildPlatformDraftPayload({
      style_adaptation: {
        target_style: 'xiaohongshu',
        adapted_title: '真实场景标题',
        adapted_selling_points: ['真实卖点'],
        adapted_detail: '真实详情',
        draft: {
          titles: ['真实场景标题', '不应保存第二个'],
          selling_points: ['真实卖点'],
          detail_copy: '真实详情',
          subtitle: '',
          promotion_copy: '',
          short_video_script: '',
        },
        platform_skill_id: 'xhs-style',
        platform_skill_version: 'v3',
      },
      generation_metadata: {
        target_style: 'xiaohongshu',
        platform_skill_id: 'xhs-style',
        platform_skill_version: 'v3',
      },
    }, undefined, {
      subtitle: '不应回填到 draft',
      promotion_copy: '不应回填到 draft',
    }, 'xiaohongshu')
    const restored = filterSinglePlatformResult(payload, 'xiaohongshu')

    expect(Object.keys((payload.style_adaptation as any).previews)).toEqual(['xiaohongshu'])
    expect((payload.draft as any).titles).toEqual(['真实场景标题'])
    expect((payload.draft as any).subtitle).toBe('')
    expect(restored.draft.promotion_copy).toBe('')
    expect(restored.generation_metadata.platform_skill_id).toBe('xhs-style')
    expect(mergePlatformDraftMeta({ selected_image_source: { user_confirmed: true } }, payload)).toMatchObject({
      selected_image_source: { user_confirmed: true },
      platform_skill_id: 'xhs-style',
      platform_skill_version: 'v3',
      platform_style: 'xiaohongshu',
    })
  })

  it('marks an editable snapshot so empty merchant fields survive reload', () => {
    const snapshot = markEditablePlatformContent({ subtitle: '', promotion_copy: '', specifications: [] })
    expect(isEditablePlatformContent(snapshot)).toBe(true)
    expect(snapshot).toMatchObject({ user_edited: true, source: 'merchant_form', subtitle: '', promotion_copy: '' })

    const generated = filterSinglePlatformResult({
      style_adaptation: {
        target_style: 'taobao',
        draft: {
          titles: ['生成标题'],
          selling_points: ['生成卖点'],
          detail_copy: '生成详情',
          subtitle: '生成副标题',
          promotion_copy: '生成推广语',
        },
      },
      extended_content: snapshot,
    }, 'taobao')
    expect(generated.draft.subtitle).toBe('生成副标题')
    expect(generated.draft.promotion_copy).toBe('生成推广语')

    const saved = buildPlatformDraftPayload(
      { style_adaptation: { target_style: 'taobao', draft: generated.draft } },
      { target_style: 'taobao' },
      snapshot,
      'taobao',
    )
    expect((saved.extended_content as any).subtitle).toBe('')
    expect((saved.extended_content as any).specifications).toEqual([])
    expect((saved.draft as any).subtitle).toBe('生成副标题')
  })
})
