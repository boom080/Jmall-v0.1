/** Best-effort session funnel. No product content or persistent user IDs. */
export type EditorStage = 'editor_opened' | 'draft_saved' | 'published' | 'no_image' | 'image_resolved'
type EditorEvent = { sessionId: string; stage: EditorStage }
type Sender = (event: EditorEvent) => Promise<unknown>

async function sendEditorEvent(event: EditorEvent) {
  const token = localStorage.getItem('jmall-token')
  if (!token) return
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 2000)
  try {
    await fetch('/api/telemetry/editor-events', {
      method: 'POST', keepalive: true, signal: controller.signal,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(event),
    })
  } finally { clearTimeout(timeout) }
}

function newSessionId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  // HTTP deployments may lack randomUUID. This is a non-security telemetry ID,
  // never a credential; metrics must not prevent the editor from mounting.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, ch => {
    const n = Math.floor(Math.random() * 16)
    return (ch === 'x' ? n : (n & 3) | 8).toString(16)
  })
}

export function createEditorFunnel(send: Sender = sendEditorEvent, sessionId = newSessionId()) {
  const recorded = new Set<EditorStage>()
  let pending = Promise.resolve()
  function record(stage: EditorStage) {
    if (recorded.has(stage)) return
    if (stage !== 'editor_opened' && !recorded.has('editor_opened')) return
    recorded.add(stage)
    // Preserve open -> stage ordering; editing/saving never awaits telemetry.
    pending = pending.then(() => send({ sessionId, stage })).then(() => {}, () => {})
  }
  return {
    open: (hasImage?: boolean) => {
      record('editor_opened')
      if (hasImage === false) record('no_image')
    },
    noImage: () => record('no_image'),
    imageResolved: () => { if (recorded.has('no_image')) record('image_resolved') },
    saved: () => record('draft_saved'),
    published: () => record('published'),
    flush: () => pending,
  }
}
