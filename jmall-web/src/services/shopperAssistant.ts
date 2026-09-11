import http from './http'

export interface ShopperIntentInterpretation {
  normalizedQuery: string
  intentSummary: string
  keywords: string[]
  categoryHints: string[]
  useCases: string[]
  maxPriceCents?: number | null
  sortBy: 'relevance' | 'popularity' | 'price_asc'
  provider: string
  model: string
  source: 'model' | 'fallback'
}

export const shopperAssistantApi = {
  parseIntent(query: string): Promise<ShopperIntentInterpretation> {
    return http.post('/ai/shopper/intent', { query })
  },
}
