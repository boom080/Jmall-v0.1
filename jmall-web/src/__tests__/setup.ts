/** Vitest global test setup.
 *
 * Configures:
 * - localStorage mock (for Pinia auth store persistence)
 * - fetch mock (for API calls in stores)
 * - Global stub for vue-router (stores don't use router directly)
 */

import { vi, afterEach } from 'vitest'

// ---- localStorage mock ----
const store: Record<string, string> = {}

vi.stubGlobal('localStorage', {
  getItem: (key: string) => store[key] ?? null,
  setItem: (key: string, value: string) => { store[key] = value },
  removeItem: (key: string) => { delete store[key] },
  clear: () => { for (const k of Object.keys(store)) delete store[k] },
  get length() { return Object.keys(store).length },
  key: (i: number) => Object.keys(store)[i] ?? null,
})

// ---- fetch mock ----
// Each test can override mockFetchValue to control responses
export const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

// ---- Clean up after each test ----
afterEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})
