// ============ Auth Types ============
export interface CurrentUser {
  id: number
  username: string
  nickname: string
  role: 'user' | 'admin'
  goldBalance: number
  pointsBalance: number
  checkinStreak: number
  storeId?: number
}

export interface LoginPayload {
  username: string
  password: string
}

export interface RegisterPayload {
  username: string
  password: string
  nickname: string
}

// ============ Product Types ============
export type ProductStatus = 'draft' | 'published'
export type PlatformStyle = 'pinduoduo' | 'taobao' | 'jd' | 'suning' | 'xiaohongshu'

/** Provenance for the single platform Skill used by an AI draft. */
export interface PlatformSkillMetadata {
  target_style?: PlatformStyle | string
  platform_skill_id?: string | null
  platform_skill_version?: string | null
  fallback?: boolean
}

/** Stable cross-platform copy shape persisted inside style_adaptation.draft. */
export interface PlatformDraft {
  titles: string[]
  selling_points: string[]
  detail_copy: string
  subtitle?: string
  price_suggestion?: number | null
  specifications?: string[]
  target_audience?: string
  usage_scenarios?: string[]
  seo_keywords?: string[]
  promotion_copy?: string
  short_video_script?: string
  pending_confirmations?: string[]
  [key: string]: unknown
}

/** Current style-adaptation envelope plus legacy compatibility fields. */
export interface PlatformStyleAdaptation extends PlatformSkillMetadata {
  target_style?: PlatformStyle | string
  adapted_title?: string
  adapted_selling_points?: string[]
  adapted_detail?: string
  visual_params?: Record<string, unknown>
  style_notes?: string
  draft?: PlatformDraft
  previews?: Record<string, PlatformStyleAdaptation>
  platform_previews?: Record<string, PlatformStyleAdaptation>
  pending_confirmations?: string[]
  [key: string]: unknown
}

export interface Product {
  id: number
  storeId: number
  storeName?: string
  title: string
  subtitle?: string
  category: string
  description: string
  price: number // 单位：分
  images: string | string[]
  style: PlatformStyle
  status: ProductStatus
  viewCount: number
  likeCount: number
  saleCount: number
  purchasable?: boolean
  unavailableReason?: string
  aiTitle?: string
  aiSellingPoints?: string | string[]
  aiDetail?: string
  // Older rows used a five-platform map; current rows use a JSON envelope.
  aiStylePreviews?: string | Record<string, unknown> | Record<PlatformStyle, StylePreview>
  marketInsights?: MarketInsight
  complianceResult?: ComplianceResult
  aiDraftMeta?: string | Record<string, unknown>
  createdAt: string
  updatedAt: string
}

export interface PublishBlocker {
  code: string
  field: string
  message: string
}

export interface PublishCheckResult {
  publishable: boolean
  publish_blockers: PublishBlocker[]
}

export interface StylePreview {
  title: string
  sellingPoints: string[]
  detail: string
  visualParams: {
    primaryColor: string
    fontSize: string
    layoutDensity: 'compact' | 'comfortable' | 'spacious'
  }
}

export interface MarketInsight {
  trends: string[]
  hotKeywords: string[]
  priceRange: { min: number; max: number; avg: number }
  suggestions: string[]
}

export interface ComplianceResult {
  passed: boolean
  warnings: string[]
  errors: string[]
}

// ============ Store Types ============
export interface Store {
  id: number
  userId: number
  name: string
  category: string
  description: string
  decorationConfig: string | Record<string, any> | null
  createdAt?: string
  updatedAt?: string
}

// ============ Transaction Types ============
export interface PurchaseResult {
  success: boolean
  productId: number
  amount: number
  multiplier: number
  goldEarned: number
  newBalance: number
  achievement?: Achievement
}

// ============ Game Types ============
export interface Achievement {
  key: string
  name: string
  description: string
  goldBonus?: number
  icon?: string
  unlocked: boolean
  unlockedAt?: string
}

/** Icon mapping for achievement keys (backend doesn't return icons) */
export const ACHIEVEMENT_ICONS: Record<string, string> = {
  FIRST_PURCHASE: '🛍️',
  COLLECTOR_10: '📦',
  BIG_SPENDER_100K: '💰',
  STREAK_7: '🔥',
  SHOP_OWNER: '🏪',
  SALE_10: '📈',
  NIGHT_OWL: '🦉',
  WHALE: '🐋',
}

export interface LeaderboardEntry {
  userId: number
  username: string
  totalSpent: number
  rank: number
}

export interface CheckinResult {
  goldReward: number
  streakDay: number
  totalGold: number
}

// ============ AI Agent Types ============
export interface AgentOrchestrateRequest {
  productInfo: {
    title: string
    category: string
    description: string
    price: number
  }
  targetStyle: PlatformStyle
  knowledgeBaseId?: string
}

export interface AgentOrchestrateResponse {
  success: boolean
  marketResearch?: MarketInsight
  copyDrafts?: Record<string, StylePreview | PlatformDraft | PlatformStyleAdaptation>
  complianceResult?: ComplianceResult
  stylePreviews?: Record<string, StylePreview | PlatformDraft | PlatformStyleAdaptation>
  style_adaptation?: PlatformStyleAdaptation
  generation_metadata?: PlatformSkillMetadata
  errors: string[]
}

export interface AiGenerateRequest {
  title: string
  category: string
  sellingPoints: string[]
  tone: string
  modelProvider?: string
  modelName?: string
  knowledgeBaseId?: string
}

export interface AiGenerateResult {
  generatedTitle: string
  highlights: string[]
  summary: string
  pendingMerchantConfirmations: string[]
  provider: string
  mock: boolean
  success: boolean
  response_source?: string
  usedChunks?: RagChunk[]
  citations?: RagChunk[]
}

export interface RagChunk {
  chunkId: string
  documentId: string
  knowledgeBaseId: string
  content: string
  score: number
  sourceFilename: string
  chunkIndex: number
}

export interface KnowledgeBase {
  id: string
  name: string
  label: string
  description: string
  documentCount: number
  chunkCount: number
  embeddingStatus: string
}

// ============ API Response ============
export interface BackendResponse<T> {
  code: number
  msg: string
  data: T
}

// ============ Cart Types ============
export interface CartItem {
  id: number
  productId: number
  title: string
  price: number
  images: string
  storeId: number
  quantity: number
  purchasable?: boolean
  unavailableReason?: string
  createdAt: string
}

// ============ Order Types ============
export interface Order {
  id: number
  productId: number
  productTitle: string
  productImage: string
  amount: number
  quantity: number
  status: 'paid' | 'shipped' | 'completed' | 'cancelled'
  createdAt: string
}

// ============ Leaderboard Types ============
export interface LeaderboardProduct {
  id: number
  title: string
  category: string
  price: number
  saleCount: number
  images: string
  storeName: string
  rank: number
}
