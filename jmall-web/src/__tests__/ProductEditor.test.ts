import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { shallowMount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import ProductEditor from '@/views/merchant/ProductEditor.vue'
import { aiImageApi } from '@/services/aiImages'

vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: {} }),
  useRouter: () => ({ replace: vi.fn(), push: vi.fn() }),
}))

describe('ProductEditor unified draft application', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))
  })
  afterEach(() => vi.unstubAllGlobals())

  it('does not re-append specifications during completion, preview application or recovery', async () => {
    const wrapper = shallowMount(ProductEditor, {
      global: { plugins: [createPinia()], config: { warnHandler: () => {} } },
    })
    await flushPromises()
    const editor = wrapper.vm as any
    const draft = {
      specifications: ['米白色帆布', '内置拉链袋', '宽35厘米，高30厘米，肩带长60厘米'],
      pending_confirmations: ['产地待商家确认'],
      subtitle: '',
    }
    for (let i = 0; i < 3; i++) {
      editor.fillExtendedCopy(draft, true)
      editor.mergeConfirmationItemsIntoSpecifications(draft, '', true)
      expect(editor.form.specifications).toBe('米白色帆布，内置拉链袋，宽35厘米，高30厘米，肩带长60厘米')
      expect(editor.form.specifications).not.toContain('待商家确认')
    }
    editor.fillExtendedCopy({ specifications: [], subtitle: '' }, true)
    expect(editor.form.specifications).toBe('')
    wrapper.unmount()
  })

  it('free recheck only calls assessment and preserves existing generated content', async () => {
    const wrapper = shallowMount(ProductEditor, {
      global: { plugins: [createPinia()], config: { warnHandler: () => {} } },
    })
    await flushPromises()
    const editor = wrapper.vm as any
    const fetchMock = vi.mocked(fetch)
    fetchMock.mockClear()
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({
      code: 10000, data: { input_assessment: { ready: true, status: 'ready', score: 85,
        understood: [], missing: [], questions: [] } },
    }) } as Response)
    editor.form.title = '帆布托特包'
    editor.form.category = '服饰鞋包'
    editor.form.specifications = '帆布；米白色'
    editor.form.targetAudience = '通勤上班族'
    editor.form.subtitle = '人工副标题'
    editor.aiFields.aiStylePreviews = 'existing skill draft'
    await editor.checkInputOnly()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/ai/input-assessment')
    expect(editor.inputAssessment.ready).toBe(true)
    expect(editor.form.subtitle).toBe('人工副标题')
    expect(editor.aiFields.aiStylePreviews).toBe('existing skill draft')
    wrapper.unmount()
  })

  it('places Image Scout beside the checks and keeps it disabled until generation completes', async () => {
    const wrapper = shallowMount(ProductEditor, {
      global: { plugins: [createPinia()], config: { warnHandler: () => {} } },
    })
    await flushPromises()
    const editor = wrapper.vm as any
    const actions = wrapper.find('.editor-actions')

    expect(actions.text()).toContain('免费检查信息')
    expect(actions.text()).toContain('AI 检查并生成')
    expect(actions.text()).toContain('根据完善内容找图')
    expect(wrapper.find('.image-scout .image-search-action').exists()).toBe(false)
    expect(editor.canSearchImageCandidates).toBe(false)
    expect(editor.imageSearchDisabledReason).toContain('请先完成 AI 检查并生成')
    expect(wrapper.find('.image-search-action-hint').text()).toContain('AI 完善信息后才能搜索图片')

    editor.form.title = '可拆洗记忆棉 U 型枕'
    editor.form.category = '家居日用'
    editor.form.subtitle = '出差通勤颈部支撑好物'
    editor.form.targetAudience = '经常出差的上班族'
    editor.form.seoKeywords = 'U 型枕，旅行枕，颈枕'
    editor.agentComplete = true
    editor.generatedPlatformStyle = 'taobao'
    editor.lastCompletedGenerationSnapshot = editor.buildImageSearchSnapshot()
    await wrapper.vm.$nextTick()

    expect(editor.canSearchImageCandidates).toBe(true)
    expect(editor.imageSearchDisabledReason).toBe('')
    wrapper.unmount()
  })

  it('invalidates the completed-generation gate after any search-relevant form edit', async () => {
    const wrapper = shallowMount(ProductEditor, {
      global: { plugins: [createPinia()], config: { warnHandler: () => {} } },
    })
    await flushPromises()
    const editor = wrapper.vm as any
    editor.form.title = '可拆洗记忆棉 U 型枕'
    editor.form.category = '家居日用'
    editor.form.subtitle = '出差通勤颈部支撑好物'
    editor.form.targetAudience = '经常出差的上班族'
    editor.agentComplete = true
    editor.generatedPlatformStyle = 'taobao'
    editor.lastCompletedGenerationSnapshot = editor.buildImageSearchSnapshot()
    await wrapper.vm.$nextTick()
    expect(editor.canSearchImageCandidates).toBe(true)

    editor.form.seoKeywords = '旅行枕，U 型枕，颈枕'
    await wrapper.vm.$nextTick()
    expect(editor.canSearchImageCandidates).toBe(false)
    expect(editor.imageSearchDisabledReason).toContain('表单已修改')
    wrapper.unmount()
  })

  it('enforces the same gate inside searchImageCandidates and sends enriched fields', async () => {
    const wrapper = shallowMount(ProductEditor, {
      global: { plugins: [createPinia()], config: { warnHandler: () => {} } },
    })
    await flushPromises()
    const editor = wrapper.vm as any
    const candidates = vi.spyOn(aiImageApi, 'candidates').mockResolvedValue({
      status: 'ready',
      query: '可拆洗记忆棉 U 型枕',
      provider: 'serpapi',
      candidates: [],
      message: '没有找到候选图片',
      disclaimer: '请核对图片使用权',
    })

    editor.form.title = '可拆洗记忆棉 U 型枕'
    editor.form.category = '家居日用'
    editor.form.subtitle = '出差通勤颈部支撑好物'
    editor.form.targetAudience = '经常出差的上班族'
    editor.form.seoKeywords = 'U 型枕，旅行枕，颈枕'

    // Direct invocation must not bypass the UI disabled state.
    await editor.searchImageCandidates()
    expect(candidates).not.toHaveBeenCalled()
    expect(editor.imageSearchMessage).toContain('请先完成 AI 检查并生成')

    editor.agentComplete = true
    editor.generatedPlatformStyle = 'taobao'
    editor.lastCompletedGenerationSnapshot = editor.buildImageSearchSnapshot()
    await editor.searchImageCandidates()

    expect(candidates).toHaveBeenCalledTimes(1)
    expect(candidates.mock.calls[0][0]).toMatchObject({
      title: '可拆洗记忆棉 U 型枕',
      subtitle: '出差通勤颈部支撑好物',
      target_audience: '经常出差的上班族',
      seo_keywords: ['U 型枕', '旅行枕', '颈枕'],
    })
    candidates.mockRestore()
    wrapper.unmount()
  })

  it('records the image-search snapshot only after the generated fields are written back', async () => {
    const wrapper = shallowMount(ProductEditor, {
      global: { plugins: [createPinia()], config: { warnHandler: () => {} } },
    })
    await flushPromises()
    const editor = wrapper.vm as any
    const fetchMock = vi.mocked(fetch)
    const finalResult = {
      overall_status: 'success',
      style_adaptation: {
        target_style: 'taobao',
        draft: {
          titles: ['可拆洗记忆棉 U 型枕｜出差通勤颈部支撑'],
          selling_points: ['可拆洗设计'],
          detail_copy: '【商品概览】\n适合出差通勤使用。',
          subtitle: '出差通勤颈部支撑好物',
          specifications: ['尺寸 30×28cm'],
          target_audience: '经常出差的上班族',
          usage_scenarios: ['飞机、高铁'],
          seo_keywords: ['U 型枕', '旅行枕', '颈枕'],
        },
      },
      generation_metadata: {
        target_style: 'taobao',
        platform_skill_id: 'taobao-copywriter',
        platform_skill_version: 'v1',
      },
    }
    let streamRead = false
    fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/ai/input-assessment')) {
        return {
          ok: true,
          json: async () => ({
            code: 10000,
            data: { input_assessment: { ready: true, status: 'ready', score: 90, questions: [] } },
          }),
        } as Response
      }
      if (url.includes('/api/ai/orchestrate/stream')) {
        const payload = `event: orchestration_complete\ndata: ${JSON.stringify({ final_result: finalResult })}\n\n`
        return {
          ok: true,
          body: {
            getReader: () => ({
              read: async () => {
                if (streamRead) return { done: true, value: undefined }
                streamRead = true
                return { done: false, value: new TextEncoder().encode(payload) }
              },
            }),
          },
        } as unknown as Response
      }
      return { ok: false } as Response
    })

    editor.form.title = '记忆棉 U 型枕'
    editor.form.category = '家居日用'
    editor.form.description = '可拆洗，适合出差通勤。'
    await editor.triggerAgent()

    expect(editor.form.subtitle).toBe('出差通勤颈部支撑好物')
    expect(editor.form.seoKeywords).toContain('U 型枕')
    expect(editor.lastCompletedGenerationSnapshot).toBe(editor.buildImageSearchSnapshot())
    expect(editor.canSearchImageCandidates).toBe(true)
    wrapper.unmount()
  })
})
