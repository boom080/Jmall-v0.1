/**
 * Shared image utilities for consistent image handling across views.
 *
 * The backend stores images as a string — either JSON array (seed data format)
 * or comma-separated (legacy ProductEditor format). This utility handles all.
 */

const CATEGORY_PLACEHOLDERS: Record<string, string> = {
  '食品饮料': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#fff3e0" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">🍪</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#e65100">食品饮料</text></svg>'),
  '生鲜水果': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#e8f5e9" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">🍎</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#2e7d32">生鲜水果</text></svg>'),
  '服饰鞋包': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#fce4ec" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">👗</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#c62828">服饰鞋包</text></svg>'),
  '家居日用': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#fff8e1" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">🏠</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#f57f17">家居日用</text></svg>'),
  '数码家电': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#e3f2fd" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">📱</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#1565c0">数码家电</text></svg>'),
  '美妆护肤': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#f3e5f5" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">💄</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#6a1b9a">美妆护肤</text></svg>'),
  '运动户外': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#e8eaf6" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">⚽</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#283593">运动户外</text></svg>'),
  '图书文娱': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#efebe9" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">📚</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#4e342e">图书文娱</text></svg>'),
  '手机数码': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#e3f2fd" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">📱</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#1565c0">手机数码</text></svg>'),
  '茶叶': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#e8f5e9" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">🍵</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#33691e">茶叶</text></svg>'),
  '厨房电器': 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#fff3e0" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">🍳</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#e65100">厨房电器</text></svg>'),
}

const DEFAULT_PLACEHOLDER = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><rect fill="#f5f5f5" width="300" height="300"/><text x="150" y="155" text-anchor="middle" font-size="48">📦</text><text x="150" y="200" text-anchor="middle" font-size="14" fill="#9e9e9e">商品图片</text></svg>')

/**
 * Extract the first image URL from various image storage formats.
 * - null/undefined/empty → placeholder
 * - JSON array string → parse and return first element
 * - comma-separated string → split and return first
 * - already an array → return first element
 */
export function getProductImage(images: any, category?: string): string {
  if (!images) return getCategoryPlaceholder(category)

  // Already an array
  if (Array.isArray(images)) {
    return images.length > 0 ? images[0] : getCategoryPlaceholder(category)
  }

  // String — could be JSON or comma-separated
  if (typeof images === 'string') {
    const trimmed = images.trim()
    if (!trimmed) return getCategoryPlaceholder(category)

    // Try JSON array first: ["url1","url2"]
    if (trimmed.startsWith('[')) {
      try {
        const arr = JSON.parse(trimmed)
        if (Array.isArray(arr) && arr.length > 0) return arr[0]
      } catch {}
    }

    // Try comma-separated
    const parts = trimmed.split(',').filter(Boolean)
    if (parts.length > 0) return parts[0].trim()
  }

  return getCategoryPlaceholder(category)
}

export function getCategoryPlaceholder(category?: string): string {
  return CATEGORY_PLACEHOLDERS[category || ''] || DEFAULT_PLACEHOLDER
}

export default { getProductImage, getCategoryPlaceholder }
