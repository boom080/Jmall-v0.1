import { afterEach, describe, expect, it, vi } from 'vitest'
import { createEditorFunnel } from '@/services/editorTelemetry'

describe('editor session funnel', () => {
  afterEach(() => vi.unstubAllGlobals())
  it('counts each reached stage once, in order, despite repeated actions', async () => {
    const send = vi.fn().mockResolvedValue(undefined)
    const funnel = createEditorFunnel(send, '84bd8b8f-b31c-4cf4-905c-509e5844be20')
    funnel.open(false)
    funnel.open(false)
    funnel.imageResolved()
    funnel.imageResolved()
    funnel.saved()
    funnel.saved()
    funnel.published()
    await funnel.flush()
    expect(send.mock.calls.map(([event]) => event.stage)).toEqual([
      'editor_opened', 'no_image', 'image_resolved', 'draft_saved', 'published',
    ])
    expect(Object.keys(send.mock.calls[0][0]).sort()).toEqual(['sessionId', 'stage'])
  })

  it('does not count existing images as no-image conversion', async () => {
    const send = vi.fn().mockResolvedValue(undefined)
    const funnel = createEditorFunnel(send)
    funnel.open(true)
    funnel.imageResolved()
    await funnel.flush()
    expect(send).toHaveBeenCalledTimes(1)
    funnel.noImage()
    funnel.imageResolved()
    await funnel.flush()
    expect(send.mock.calls.map(([event]) => event.stage)).toEqual(['editor_opened', 'no_image', 'image_resolved'])
  })

  it('does not report actions before initialization and swallows transport failures', async () => {
    const send = vi.fn().mockRejectedValue(new Error('offline'))
    const funnel = createEditorFunnel(send)
    funnel.saved()
    funnel.imageResolved()
    await funnel.flush()
    expect(send).not.toHaveBeenCalled()
    funnel.open()
    funnel.saved()
    await expect(funnel.flush()).resolves.toBeUndefined()
  })

  it('still mounts on HTTP origins without randomUUID', async () => {
    vi.stubGlobal('crypto', undefined)
    const send = vi.fn().mockResolvedValue(undefined)
    const funnel = createEditorFunnel(send)
    funnel.open()
    await funnel.flush()
    expect(send.mock.calls[0][0].sessionId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/)
  })
})
