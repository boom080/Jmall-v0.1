<template>
  <div class="product-feed">
    <section class="discovery-hero" aria-labelledby="feed-title">
      <div class="hero-glow hero-glow-one" aria-hidden="true"></div>
      <div class="hero-glow hero-glow-two" aria-hidden="true"></div>
      <div class="hero-copy">
        <div class="hero-kicker">
          <span class="kicker-dot"></span>
          <span>今日营业中 · 好物刚刚刷新</span>
        </div>
        <h1 id="feed-title">今天也来逛点好东西吧！</h1>
        <p>发现好物，收集灵感，把每一次浏览都变成小小的惊喜。</p>
        <div class="hero-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜商品、店铺或灵感…"
            clearable
            size="large"
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button @click="onSearch" :loading="loading">
                <el-icon><Search /></el-icon>
                搜索好物
              </el-button>
            </template>
          </el-input>
        </div>
        <div class="hotwords" aria-label="热门搜索">
          <span>大家在找</span>
          <button v-for="word in hotwords" :key="word" type="button" @click="useHotword(word)">
            {{ word }}
          </button>
        </div>
      </div>
      <div class="hero-mascot" aria-hidden="true">
        <div class="mascot-speech">AI 店员在帮你挑 ✦</div>
        <div class="mascot-orbit orbit-one"></div>
        <div class="mascot-orbit orbit-two"></div>
        <JmallMascot variant="wave" :size="148" label="Jmall 吉祥物" />
      </div>
    </section>

    <section class="mission-card" aria-label="今日浏览任务">
      <div class="mission-icon"><span>✦</span></div>
      <div class="mission-copy">
        <div class="mission-title-row">
          <strong>{{ missionCompleted ? '任务完成，今天的眼光真不错！' : '今日小任务 · 逛逛好物' }}</strong>
          <span class="mission-reward">✦ 今日发现进度</span>
        </div>
        <p>{{ missionCompleted ? '浏览进度已完成，继续发现下一件心动好物吧。' : '浏览 3 件商品，完成今天的发现目标' }}</p>
        <div class="mission-progress" role="progressbar" :aria-valuenow="missionProgress" aria-valuemin="0" aria-valuemax="3">
          <span class="progress-track"><i :style="{ width: `${missionProgress / 3 * 100}%` }"></i></span>
          <span class="progress-count">{{ missionProgress }}/3</span>
        </div>
      </div>
      <div class="mission-mascot"><JmallMascot :variant="missionCompleted ? 'celebrate' : 'idle'" :size="62" animated /></div>
      <span v-if="missionCompleted" class="mission-done">已完成 ✓</span>
    </section>

    <section class="feed-toolbar" aria-label="商品筛选">
      <div class="section-heading">
        <span class="section-eyebrow">灵感货架</span>
        <div class="heading-line">
          <h2>为你挑的好物</h2>
          <span class="result-count">{{ resultCountLabel }}</span>
        </div>
      </div>
      <div class="feed-filters">
        <button
          v-for="filter in feedFilters"
          :key="filter.id"
          type="button"
          class="filter-pill"
          :class="{ active: activeFeedFilter === filter.id }"
          @click="setFeedFilter(filter.id)"
        >
          <span>{{ filter.icon }}</span>{{ filter.label }}
        </button>
      </div>
    </section>

    <div class="style-filters" aria-label="平台风格筛选">
      <span class="style-filter-label">内容风格</span>
      <button
        v-for="style in styleFilters"
        :key="style.id"
        type="button"
        class="style-pill"
        :class="{ active: activeStyle === style.id }"
        @click="setStyle(style.id)"
      >
        <span>{{ style.icon }}</span>{{ style.label }}
      </button>
    </div>

    <div v-if="loading" class="loading-grid" aria-label="商品加载中">
      <article v-for="index in 8" :key="index" class="loading-card">
        <div class="loading-image shimmer"></div>
        <div class="loading-lines">
          <span class="shimmer"></span>
          <span class="shimmer short"></span>
          <span class="shimmer price"></span>
        </div>
      </article>
    </div>

    <el-result
      v-else-if="error"
      class="feed-result"
      icon="error"
      title="好物暂时迷路了"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadProducts">🔄 再试一次</el-button>
      </template>
    </el-result>

    <div v-else-if="displayedProducts.length" class="product-grid">
      <article
        v-for="product in displayedProducts"
        :key="product.id"
        class="product-card"
        :class="[`card-style-${product.style}`, { visited: visitedIds.includes(product.id) }]"
        @click="viewDetail(product.id)"
      >
        <div class="card-image">
          <img
            :src="getProductImage(product.images, product.category)"
            :alt="product.title"
            loading="lazy"
            @error="onImageError($event, product.category)"
          />
          <div class="image-shade" aria-hidden="true"></div>
          <span class="rarity-tag" :class="rarityClass(product)">{{ rarityLabel(product) }}</span>
          <span v-if="styleLabel(product.style)" class="style-tag">{{ styleLabel(product.style) }}</span>
          <button
            type="button"
            class="favorite-button"
            :class="{ active: isFavorite(product.id) }"
            :aria-label="isFavorite(product.id) ? '取消收藏' : '收藏商品'"
            @click.stop="toggleFavorite(product.id)"
          >
            {{ isFavorite(product.id) ? '♥' : '♡' }}
          </button>
        </div>
        <div class="card-body">
          <div class="card-category-row">
            <span class="card-category">{{ product.category || '精选好物' }}</span>
            <span class="card-level">{{ product.viewCount ? `已有 ${formatCount(product.viewCount)} 人看过` : '新发现' }}</span>
          </div>
          <h3 class="card-title">{{ product.title }}</h3>
          <p v-if="product.subtitle" class="card-subtitle">{{ product.subtitle }}</p>
          <p v-if="descriptionPreview(product)" class="card-summary">{{ descriptionPreview(product) }}</p>
          <div v-if="sellingPoints(product).length" class="card-highlights">
            <span v-for="point in sellingPoints(product).slice(0, 2)" :key="point">{{ point }}</span>
          </div>
          <div class="card-meta">
            <span>👁 {{ formatCount(product.viewCount) }}</span>
            <span>📦 {{ formatCount(product.saleCount) }} 已售</span>
          </div>
          <div class="card-footer">
            <div>
              <span class="price-currency">¥</span>
              <span class="card-price">{{ formatPrice(product.price) }}</span>
            </div>
            <span class="view-detail">去看看 <span>→</span></span>
          </div>
          <p v-if="product.storeName" class="card-store">🏪 {{ product.storeName }}</p>
        </div>
      </article>
    </div>

    <el-empty v-else class="feed-empty" description="还没有找到合适的好物">
      <template #image>
        <JmallMascot variant="idle" :size="92" :animated="false" />
      </template>
      <el-button type="primary" @click="$router.push('/merchant/products/new')">🏪 去上架第一件商品</el-button>
    </el-empty>

    <div v-if="!loading && !error && total > pageSize" class="pagination">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="onPageChange"
      />
    </div>

    <div class="feed-helper" aria-label="AI 店员提示">
      <JmallMascot variant="mark" :size="40" :animated="false" />
      <span>不知道逛什么？<strong>让 AI 店员带你逛</strong></span>
      <button type="button" @click="openAssistant">试试看 →</button>
    </div>

    <el-dialog
      v-model="assistantOpen"
      class="ai-shopper-dialog"
      width="520px"
      append-to-body
      :show-close="false"
      :close-on-click-modal="true"
      aria-label="AI 店员带你逛"
    >
      <div class="assistant-dialog-content">
        <div class="assistant-dialog-header">
          <div class="assistant-dialog-mascot">
            <JmallMascot variant="wave" :size="62" label="AI 店员" />
          </div>
          <div class="assistant-dialog-title">
            <span class="assistant-eyebrow">Jmall 灵感导购</span>
            <h3>AI 店员带你逛</h3>
            <p>告诉我场景、预算或品类，我从当前好物里帮你挑。</p>
          </div>
          <button type="button" class="assistant-close" aria-label="关闭 AI 店员" @click="assistantOpen = false">×</button>
        </div>

        <div class="assistant-chat">
          <div class="assistant-bubble">
            <JmallMascot variant="mark" :size="24" :animated="false" />
            <span>想看什么？给我一个小线索，我会给你最多 3 个选择。</span>
          </div>

          <div class="assistant-quick-intents" aria-label="快捷需求">
            <span>可以试试</span>
            <button
              v-for="intent in assistantQuickIntents"
              :key="intent.label"
              type="button"
              @click="askAssistant(intent.query)"
            >
              {{ intent.label }}
            </button>
          </div>

          <div class="assistant-input-row">
            <el-input
              v-model="assistantInput"
              class="assistant-input"
              placeholder="例如：通勤用，预算 100 元以内"
              maxlength="80"
              show-word-limit
              clearable
              @keyup.enter="askAssistant()"
            />
            <el-button type="primary" :loading="assistantLoading" @click="askAssistant()">帮我挑</el-button>
          </div>
          <p v-if="assistantNotice" class="assistant-notice" :class="{ warning: assistantNoticeType === 'warning' }">
            {{ assistantNotice }}
          </p>
        </div>

        <div v-if="assistantLoading" class="assistant-loading" aria-live="polite">
          <JmallMascot variant="wave" :size="54" />
          <div>
            <strong>正在翻找货架…</strong>
            <span>看看哪几件最适合你</span>
          </div>
        </div>

        <div v-else-if="assistantSearched" class="assistant-results" aria-live="polite">
          <div class="assistant-results-heading">
            <div>
              <span class="assistant-eyebrow">店员推荐</span>
              <h4>{{ assistantResultTitle }}</h4>
            </div>
            <span class="assistant-result-count">{{ assistantRecommendations.length }}/3 件</span>
          </div>

          <div v-if="assistantRecommendations.length" class="assistant-recommendations">
            <button
              v-for="product in assistantRecommendations"
              :key="product.id"
              type="button"
              class="assistant-product-option"
              @click="chooseAssistantProduct(product.id)"
            >
              <img
                :src="getProductImage(product.images, product.category)"
                :alt="product.title"
                @error="onImageError($event, product.category)"
              />
              <span class="assistant-product-copy">
                <strong>{{ product.title }}</strong>
                <span>{{ assistantProductReason(product) }}</span>
                <b>¥{{ formatPrice(product.price) }}</b>
              </span>
              <span class="assistant-option-arrow">→</span>
            </button>
          </div>

          <div v-else class="assistant-no-results">
            <JmallMascot variant="idle" :size="54" :animated="false" />
            <p>{{ assistantEmptyMessage }}</p>
            <button type="button" @click="assistantInput = ''; assistantSearched = false; assistantNotice = ''">换个说法试试</button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { productApi } from '@/services/products'
import { shopperAssistantApi, type ShopperIntentInterpretation } from '@/services/shopperAssistant'
import http from '@/services/http'
import { getCategoryPlaceholder, getProductImage } from '@/services/imageUtils'
import type { Product } from '@/types'
import JmallMascot from '@/components/brand/JmallMascot.vue'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const VISITED_KEY = 'jmall-v03-session-visited-products'

function loadVisitedIds(): number[] {
  try {
    const stored = JSON.parse(sessionStorage.getItem(VISITED_KEY) || '[]')
    return Array.isArray(stored) ? stored.map(Number).filter(Number.isFinite) : []
  } catch { return [] }
}

const products = ref<Product[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const activeStyle = ref('all')
const activeFeedFilter = ref('all')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const visitedIds = ref<number[]>(loadVisitedIds())
const favoriteIds = ref<number[]>([])
const assistantOpen = ref(false)
const assistantInput = ref('')
const assistantLoading = ref(false)
const assistantSearched = ref(false)
const assistantRecommendations = ref<Product[]>([])
const assistantResultTitle = ref('这几件可能适合你')
const assistantEmptyMessage = ref('暂时没有找到合适的商品，换个场景或品类试试看吧。')
const assistantNotice = ref('')
const assistantNoticeType = ref<'info' | 'warning'>('info')
const assistantResolvedRequest = ref<AssistantRequest | null>(null)

const hotwords = ['通勤好物', '桌面氛围感', '送礼灵感']
const assistantQuickIntents = [
  { label: '通勤实用', query: '通勤实用' },
  { label: '百元以内', query: '百元以内' },
  { label: '送礼灵感', query: '送礼' },
  { label: '人气好物', query: '人气爆款' },
  { label: '数码 / 食品', query: '数码或食品' },
]
const feedFilters = [
  { id: 'all', label: '全部好物', icon: '✦' },
  { id: 'recommend', label: '今日推荐', icon: '☀' },
  { id: 'new', label: '新品掉落', icon: '✿' },
  { id: 'popular', label: '人气榜', icon: '♡' },
]
const styleFilters = [
  { id: 'all', label: '全部风格', icon: '✦' },
  { id: 'pinduoduo', label: '拼多多风', icon: '🔴' },
  { id: 'taobao', label: '淘宝风', icon: '🟠' },
  { id: 'jd', label: '京东风', icon: '🔵' },
  { id: 'suning', label: '苏宁风', icon: '🟦' },
  { id: 'xiaohongshu', label: '小红书风', icon: '💗' },
]

const STYLE_LABELS: Record<string, string> = {
  pinduoduo: '拼多多风', taobao: '淘宝风', jd: '京东风',
  suning: '苏宁风', xiaohongshu: '小红书风',
}

const missionProgress = computed(() => Math.min(3, visitedIds.value.length))
const missionCompleted = computed(() => missionProgress.value >= 3)
const resultCountLabel = computed(() => total.value ? `${total.value} 件好物` : `${products.value.length} 件好物`)
const displayedProducts = computed(() => {
  const list = [...products.value]
  if (activeFeedFilter.value === 'new') return list.sort((a, b) => b.id - a.id)
  if (activeFeedFilter.value === 'popular') return list.sort((a, b) => (b.saleCount + b.viewCount) - (a.saleCount + a.viewCount))
  if (activeFeedFilter.value === 'recommend') return list.sort((a, b) => (b.likeCount + b.viewCount) - (a.likeCount + a.viewCount))
  return list
})

function styleLabel(style: string) { return STYLE_LABELS[style] || '' }

function formatPrice(price: number): string {
  return ((price || 0) / 100).toFixed(2)
}

function formatCount(value: number): string {
  const count = value || 0
  if (count >= 10000) return `${(count / 10000).toFixed(1)}万`
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`
  return count.toLocaleString()
}

function sellingPoints(product: Product): string[] {
  const raw = product.aiSellingPoints
  if (Array.isArray(raw)) return raw.map(String).filter(Boolean)
  if (typeof raw !== 'string' || !raw.trim()) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.map(String).filter(Boolean) : []
  } catch { return [] }
}

function descriptionPreview(product: Product): string {
  const source = String(product.description || product.aiDetail || '')
    .replace(/【[^】]+】/g, ' ')
    .replace(/[•\n\r]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
  if (!source || source === String(product.subtitle || '').trim()) return ''
  return source
}

function rarityClass(product: Product): string {
  if ((product.saleCount || 0) >= 100) return 'rare-gold'
  if ((product.viewCount || 0) >= 50) return 'rare-blue'
  return 'fresh'
}

function rarityLabel(product: Product): string {
  if ((product.saleCount || 0) >= 100) return '人气爆款'
  if ((product.viewCount || 0) >= 50) return '正在升温'
  return '新发现'
}

function isFavorite(id: number) { return favoriteIds.value.includes(id) }

async function toggleFavorite(id: number) {
  if (!authStore.isAuthenticated) {
    ElMessage.info('登录后才能收藏好物')
    router.push({ path: '/login', query: { redirect: '/shop' } })
    return
  }
  try {
    if (isFavorite(id)) {
      await http.delete(`/collections/${id}`)
      favoriteIds.value = favoriteIds.value.filter(item => item !== id)
      ElMessage.info('已取消收藏')
    } else {
      await http.post(`/collections/${id}`)
      favoriteIds.value = [...favoriteIds.value, id]
      ElMessage.success('已收藏，稍后再来看看吧')
    }
  } catch (error: any) {
    ElMessage.error(error?.message || '收藏操作失败')
  }
}

function useHotword(word: string) {
  searchKeyword.value = word
  onSearch()
}

type AssistantIntent = 'commute' | 'gift' | 'digital' | 'food' | 'home' | 'beauty' | 'clothing' | 'play' | 'popular' | 'budget'

const ASSISTANT_INTENT_TERMS: Record<AssistantIntent, string[]> = {
  commute: ['通勤', '上班', '办公', '办公室', '出行', '便携', '随身', '桌面'],
  gift: ['送礼', '礼物', '礼盒', '送给', '生日', '节日'],
  digital: ['数码', '手机', '电脑', '耳机', '相机', '智能', '充电', '科技', '家电'],
  food: ['食品', '饮料', '零食', '茶', '牛奶', '咖啡', '早餐', '下午茶', '吃', '喝'],
  home: ['家居', '家用', '居家', '厨房', '清洁', '日用'],
  beauty: ['美妆', '护肤', '精油', '香氛'],
  clothing: ['服饰', '衣服', '穿搭', '鞋', '包'],
  play: ['玩', '游戏', '娱乐', '休闲'],
  popular: ['人气', '热门', '爆款', '畅销', '热卖', '大家都在买'],
  budget: ['预算', '便宜', '实惠', '以内', '以下'],
}

const ASSISTANT_STOP_WORDS = new Set(['帮我', '想要', '想看', '推荐', '一下', '一些', '适合', '的', '或', '和', '要'])

interface AssistantRequest {
  terms: string[]
  intents: AssistantIntent[]
  maxPriceCents?: number
  intentSummary?: string
  source?: 'model' | 'fallback' | 'local'
  sortBy?: 'relevance' | 'popularity' | 'price_asc'
}

interface AssistantRanking {
  products: Product[]
  matched: boolean
  maxPriceCents?: number
}

function parseAssistantBudget(query: string): number | undefined {
  const normalized = query.replace(/\s+/g, '')
  if (/(?:百|一百)元/.test(normalized)) return 100 * 100
  if (/(?:两百|二百)元/.test(normalized)) return 200 * 100
  if (/(?:三百|三百)元/.test(normalized)) return 300 * 100

  const withUnit = normalized.match(/(\d+(?:\.\d+)?)\s*(?:元|块|¥|￥)\s*(?:以内|以下|内)?/)
  const withBudgetPrefix = normalized.match(/(?:预算|不超过|低于|少于|以内|以下)\s*(\d+(?:\.\d+)?)/)
  const amount = withUnit?.[1] || withBudgetPrefix?.[1]
  if (!amount) return undefined
  const yuan = Number(amount)
  return Number.isFinite(yuan) && yuan >= 0 ? Math.round(yuan * 100) : undefined
}

function extractAssistantTerms(query: string): string[] {
  const terms = new Set<string>()
  const chunks = query
    .toLowerCase()
    .split(/[\s,，。！？、；;:：/\\|]+/)
    .map(item => item.trim())
    .filter(Boolean)

  for (const chunk of chunks) {
    if (ASSISTANT_STOP_WORDS.has(chunk) || /^\d+(?:\.\d+)?(?:元|块)?$/.test(chunk)) continue
    if (/^[\u4e00-\u9fff]+$/.test(chunk)) {
      if (chunk.length >= 2 && !ASSISTANT_STOP_WORDS.has(chunk)) terms.add(chunk)
      for (let index = 0; index < chunk.length - 1; index += 1) {
        const pair = chunk.slice(index, index + 2)
        if (!ASSISTANT_STOP_WORDS.has(pair)) terms.add(pair)
      }
    } else {
      terms.add(chunk)
    }
  }

  return Array.from(terms).filter(term => term.length > 1)
}

function parseAssistantRequest(query: string, semantic?: ShopperIntentInterpretation | null): AssistantRequest {
  const semanticText = semantic
    ? [semantic.normalizedQuery, ...semantic.keywords, ...semantic.categoryHints, ...semantic.useCases].join(' ')
    : ''
  const combinedQuery = `${query} ${semanticText}`.trim()
  const normalized = combinedQuery.toLowerCase().replace(/\s+/g, '')
  const intents = (Object.keys(ASSISTANT_INTENT_TERMS) as AssistantIntent[])
    .filter(intent => ASSISTANT_INTENT_TERMS[intent].some(term => normalized.includes(term)))
  const intentTerms = intents.flatMap(intent => ASSISTANT_INTENT_TERMS[intent])
    .filter(term => normalized.includes(term))

  return {
    terms: Array.from(new Set([...extractAssistantTerms(combinedQuery), ...intentTerms])),
    intents,
    maxPriceCents: semantic?.maxPriceCents == null ? parseAssistantBudget(query) : Number(semantic.maxPriceCents),
    intentSummary: semantic?.intentSummary,
    source: semantic?.source || 'local',
    sortBy: semantic?.sortBy || 'relevance',
  }
}

function assistantProductText(product: Product): string {
  return [
    product.title,
    product.subtitle,
    product.category,
    product.description,
    product.aiTitle,
    product.aiDetail,
    product.storeName,
    ...sellingPoints(product),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
}

function assistantPopularity(product: Product): number {
  return (product.saleCount || 0) * 3 + (product.viewCount || 0) + (product.likeCount || 0) * 2
}

function rankAssistantProducts(candidates: Product[], request: AssistantRequest): AssistantRanking {
  const budgetCandidates = request.maxPriceCents === undefined
    ? candidates
    : candidates.filter(product => Number(product.price) <= request.maxPriceCents!)

  if (!budgetCandidates.length) {
    return { products: [], matched: false, maxPriceCents: request.maxPriceCents }
  }

  const scored = budgetCandidates.map(product => {
    const text = assistantProductText(product)
    const matchedTerms = request.terms.filter(term => text.includes(term))
    const matchedIntents = request.intents.filter(intent =>
      ASSISTANT_INTENT_TERMS[intent].some(term => text.includes(term)),
    )
    let score = matchedTerms.reduce((sum, term) => sum + (term.length >= 3 ? 12 : 5), 0)
    score += matchedIntents.length * 11
    score += Math.min(28, assistantPopularity(product) / 12)
    if (request.intents.includes('popular')) score += Math.min(36, assistantPopularity(product) / 8)
    if (request.maxPriceCents !== undefined) {
      const priceRatio = Number(product.price) / Math.max(request.maxPriceCents, 1)
      score += priceRatio <= 0.7 ? 8 : 3
    }
    return { product, score, matched: matchedTerms.length > 0 || matchedIntents.length > 0 }
  })

  const matched = scored.some(item => item.matched)
  scored.sort((left, right) => {
    if (request.sortBy === 'price_asc') return Number(left.product.price) - Number(right.product.price)
    if (request.sortBy === 'popularity') return assistantPopularity(right.product) - assistantPopularity(left.product)
    return right.score - left.score || assistantPopularity(right.product) - assistantPopularity(left.product)
  })
  return {
    products: scored.filter(item => matched ? item.matched : true).map(item => item.product),
    matched,
    maxPriceCents: request.maxPriceCents,
  }
}

function assistantBudgetLabel(maxPriceCents?: number): string {
  if (maxPriceCents === undefined) return ''
  const yuan = maxPriceCents / 100
  return `${yuan.toFixed(yuan % 1 ? 2 : 0)} 元以内`
}

async function fetchAssistantProducts(): Promise<Product[]> {
  const result: any = await productApi.list({ status: 'published', page: 1, size: 50 })
  const records = result?.records || result?.items || (Array.isArray(result) ? result : [])
  // The status query is the source of truth; tolerate compact API payloads that omit status.
  return (Array.isArray(records) ? records : []).filter((product: Product) => product && (!product.status || product.status === 'published'))
}

function openAssistant() {
  assistantOpen.value = true
  assistantInput.value = ''
  assistantLoading.value = false
  assistantSearched.value = false
  assistantRecommendations.value = []
  assistantResolvedRequest.value = null
  assistantNotice.value = ''
  assistantResultTitle.value = '这几件可能适合你'
}

async function askAssistant(query?: string) {
  if (assistantLoading.value) return
  const requestText = (query ?? assistantInput.value).trim()
  if (!requestText) {
    assistantNoticeType.value = 'warning'
    assistantNotice.value = '告诉我预算、场景或品类吧，例如“通勤用，预算 100 元以内”。'
    ElMessage.info('先告诉 AI 店员你想看什么吧')
    return
  }

  assistantInput.value = requestText
  assistantLoading.value = true
  assistantSearched.value = true
  assistantRecommendations.value = []
  assistantNotice.value = ''
  assistantNoticeType.value = 'info'

  const [catalogResult, intentResult] = await Promise.allSettled([
    fetchAssistantProducts(),
    shopperAssistantApi.parseIntent(requestText),
  ])

  let candidates: Product[] = []
  if (catalogResult.status === 'fulfilled') {
    candidates = catalogResult.value
  } else {
    // The discovery shelf is still a useful local fallback when the wider query fails.
    candidates = products.value.filter(product => !product.status || product.status === 'published')
    if (!candidates.length) {
      assistantNoticeType.value = 'warning'
      assistantNotice.value = '货架暂时连接不上，请稍后再试。'
    }
  }

  const semantic = intentResult.status === 'fulfilled' ? intentResult.value : null
  const request = parseAssistantRequest(requestText, semantic)
  assistantResolvedRequest.value = request
  const ranking = rankAssistantProducts(candidates, request)
  assistantRecommendations.value = ranking.products.slice(0, 3)
  if (!assistantRecommendations.value.length) {
    assistantEmptyMessage.value = ranking.maxPriceCents === undefined
      ? '当前货架还没有符合描述的已发布商品，换个品类或场景试试吧。'
      : `当前没有 ${assistantBudgetLabel(ranking.maxPriceCents)} 的已发布商品，放宽预算再试试看吧。`
    assistantResultTitle.value = '这次还没找到合适的好物'
  } else if (!ranking.matched) {
    assistantResultTitle.value = request.maxPriceCents === undefined ? '先给你看看最近的人气好物' : '预算内的人气好物'
    assistantNotice.value = request.intentSummary
      ? `AI 理解为“${request.intentSummary}”，当前货架没有完全匹配，先给你看看相近的人气好物。`
      : '没有完全匹配的描述，店员先按人气给你挑了几件。'
  } else if (request.maxPriceCents !== undefined) {
    assistantResultTitle.value = `为你挑的 ${assistantBudgetLabel(request.maxPriceCents)} 好物`
    if (request.intentSummary) assistantNotice.value = `AI 已理解：${request.intentSummary}`
  } else {
    assistantResultTitle.value = '这几件可能正合你心意'
    if (request.intentSummary) assistantNotice.value = `AI 已理解：${request.intentSummary}`
  }
  assistantLoading.value = false
}

function assistantProductReason(product: Product): string {
  const request = assistantResolvedRequest.value || parseAssistantRequest(assistantInput.value)
  if (request.maxPriceCents !== undefined && product.price <= request.maxPriceCents) return '符合你的预算'
  const text = assistantProductText(product)
  const matchedIntent = request.intents.find(intent => ASSISTANT_INTENT_TERMS[intent].some(term => text.includes(term)))
  if (matchedIntent === 'commute') return '通勤场景更搭'
  if (matchedIntent === 'gift') return '送礼拿得出手'
  if (matchedIntent === 'digital') return '数码控可以看看'
  if (matchedIntent === 'food') return '适合吃喝囤货'
  if (matchedIntent === 'home') return '居家场景更合适'
  if (matchedIntent === 'beauty') return '美妆护理方向匹配'
  if (matchedIntent === 'clothing') return '穿搭需求更匹配'
  if (matchedIntent === 'play') return '更贴近休闲娱乐需求'
  if (matchedIntent === 'popular' || !request.terms.length) return '最近人气正在上升'
  const matchingTerm = request.terms.find(term => text.includes(term))
  return matchingTerm ? `包含“${matchingTerm}”相关信息` : '从当前货架为你精选'
}

function chooseAssistantProduct(id: number) {
  assistantOpen.value = false
  viewDetail(id)
}

function setStyle(style: string) {
  if (activeStyle.value === style) return
  activeStyle.value = style
  currentPage.value = 1
  loadProducts()
}

function setFeedFilter(filter: string) {
  activeFeedFilter.value = filter
}

async function loadProducts() {
  loading.value = true
  error.value = null
  try {
    const params: any = { page: currentPage.value, size: pageSize.value, status: 'published' }
    if (activeStyle.value !== 'all') params.style = activeStyle.value
    if (searchKeyword.value.trim()) params.keyword = searchKeyword.value.trim()
    const result: any = await productApi.list(params)
    products.value = result.records || result.items || (Array.isArray(result) ? result : [])
    total.value = result.total || products.value.length
  } catch (e: any) {
    error.value = e.message || '加载失败'
    products.value = []
  } finally {
    loading.value = false
  }
}

function onSearch() {
  currentPage.value = 1
  loadProducts()
}

function viewDetail(id: number) {
  if (!visitedIds.value.includes(id)) {
    visitedIds.value = [...visitedIds.value, id]
    sessionStorage.setItem(VISITED_KEY, JSON.stringify(visitedIds.value))
    if (visitedIds.value.length === 3) ElMessage.success('今日浏览进度完成 ✦')
  }
  router.push(`/shop/product/${id}`)
}

function onPageChange(page: number) {
  currentPage.value = page
  loadProducts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onImageError(event: Event, category: string) {
  const image = event.target as HTMLImageElement
  if (image.dataset.fallbackApplied) return
  image.dataset.fallbackApplied = 'true'
  image.src = getCategoryPlaceholder(category)
}

async function loadFavorites() {
  if (!authStore.isAuthenticated) return
  try {
    const items = await http.get('/collections')
    favoriteIds.value = (Array.isArray(items) ? items : [])
      .map((item: any) => Number(item.productId || item.product?.id || item.id))
      .filter(Number.isFinite)
  } catch { /* favorite state is optional on the discovery page */ }
}

onMounted(() => {
  loadProducts()
  loadFavorites()
})
</script>

<style scoped>
.product-feed {
  --feed-plum: #342b4a;
  --feed-muted: #867b91;
  --feed-line: #f0e3dd;
  --feed-pink: #ff4d63;
  --feed-coral: #ff6b81;
  --feed-lavender: #8b78d8;
  --feed-yellow: #ffd75e;
  max-width: 1440px;
  margin: 0 auto;
  padding: 24px 32px 78px;
  color: var(--feed-plum);
}

.discovery-hero {
  position: relative;
  display: flex;
  min-height: 306px;
  overflow: hidden;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  padding: 42px 68px 42px 70px;
  border: 1px solid rgba(255,255,255,.82);
  border-radius: 32px;
  background: linear-gradient(117deg, #fff0df 0%, #ffe4ee 48%, #eae4ff 100%);
  box-shadow: 0 18px 42px rgba(93, 66, 110, .11);
}

.hero-glow { position: absolute; border-radius: 50%; pointer-events: none; }
.hero-glow-one { width: 260px; height: 260px; right: 14%; top: -126px; background: rgba(255,255,255,.48); }
.hero-glow-two { width: 190px; height: 190px; right: -44px; bottom: -95px; background: rgba(255, 153, 180, .25); }
.hero-copy { position: relative; z-index: 1; max-width: 730px; }
.hero-kicker { display: inline-flex; align-items: center; gap: 8px; margin-bottom: 12px; color: #a65476; font-size: 13px; font-weight: 700; letter-spacing: .04em; }
.kicker-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--feed-coral); box-shadow: 0 0 0 5px rgba(255, 107, 129, .13); }
.hero-copy h1 { margin: 0; color: var(--feed-plum); font-size: clamp(31px, 4vw, 46px); line-height: 1.18; letter-spacing: -.045em; }
.hero-copy p { margin: 12px 0 22px; color: #756b7b; font-size: 16px; line-height: 1.65; }
.hero-search { max-width: 700px; }
.hero-search :deep(.el-input) { --el-input-height: 52px; }
.hero-search :deep(.el-input__wrapper) { border: 1px solid rgba(255,255,255,.92); border-radius: 16px 0 0 16px; box-shadow: 0 8px 22px rgba(114, 81, 101, .11); }
.hero-search :deep(.el-input__inner) { color: var(--feed-plum); font-size: 15px; }
.hero-search :deep(.el-input-group__append) { padding: 0; border: 0; border-radius: 0 16px 16px 0; background: var(--feed-pink); box-shadow: 0 8px 22px rgba(255, 77, 99, .2); }
.hero-search :deep(.el-input-group__append .el-button) { height: 52px; padding: 0 20px; border-radius: 0 16px 16px 0; color: #fff; font-weight: 700; background: var(--feed-pink); }
.hotwords { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 14px; color: #9b8190; font-size: 12px; }
.hotwords button { padding: 0; border: 0; color: #8e6680; background: transparent; cursor: pointer; font-size: 12px; }
.hotwords button:hover { color: var(--feed-pink); text-decoration: underline; }

.hero-mascot { position: relative; z-index: 1; display: grid; flex: 0 0 190px; place-items: center; align-self: stretch; padding-top: 12px; }
.hero-mascot :deep(.jmall-mascot) { filter: drop-shadow(0 14px 12px rgba(198, 87, 118, .2)); }
.mascot-speech { position: absolute; z-index: 3; top: 15px; right: -3px; padding: 9px 14px; border-radius: 14px 14px 4px 14px; color: #fff; background: var(--feed-plum); box-shadow: 0 8px 16px rgba(52,43,74,.16); font-size: 12px; font-weight: 700; white-space: nowrap; }
.mascot-orbit { position: absolute; border: 1px dashed rgba(198, 87, 118, .28); border-radius: 50%; transform: rotate(-14deg); }
.orbit-one { width: 168px; height: 96px; }
.orbit-two { width: 186px; height: 124px; border-color: rgba(255, 215, 94, .45); transform: rotate(28deg); }

.mission-card { display: flex; align-items: center; gap: 15px; min-height: 96px; margin: 20px 0 30px; padding: 16px 22px; border: 1px solid #f3e4c8; border-radius: 21px; background: linear-gradient(102deg, #fffaf0, #fff6e8 60%, #fffdf7); box-shadow: 0 8px 20px rgba(158, 117, 65, .07); }
.mission-icon { display: grid; flex: 0 0 46px; width: 46px; height: 46px; place-items: center; border-radius: 15px; color: #a96f13; background: #ffedaa; font-size: 25px; }
.mission-copy { flex: 1; min-width: 0; }
.mission-title-row { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; }
.mission-title-row strong { color: var(--feed-plum); font-size: 15px; }
.mission-reward { padding: 4px 9px; border-radius: 999px; color: #a66b12; background: #ffedb0; font-size: 11px; font-weight: 800; }
.mission-copy p { margin: 5px 0 9px; color: var(--feed-muted); font-size: 12px; }
.mission-progress { display: flex; align-items: center; gap: 9px; max-width: 360px; }
.progress-track { display: block; flex: 1; height: 7px; overflow: hidden; border-radius: 99px; background: #f3e4cb; }
.progress-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #ffbd65, #ff6b81); transition: width .4s ease; }
.progress-count { color: #aa7a37; font-size: 11px; font-weight: 800; }
.mission-mascot { align-self: flex-end; margin-bottom: -5px; }
.mission-done { padding: 7px 10px; border-radius: 12px; color: #41876b; background: #e8f8ed; font-size: 11px; font-weight: 800; white-space: nowrap; }

.feed-toolbar { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 14px; }
.section-eyebrow { color: #ba7384; font-size: 11px; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; }
.heading-line { display: flex; align-items: baseline; gap: 12px; margin-top: 5px; }
.heading-line h2 { margin: 0; color: var(--feed-plum); font-size: 27px; letter-spacing: -.035em; }
.result-count { color: #a59aa8; font-size: 12px; }
.feed-filters, .style-filters { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.feed-filters { justify-content: flex-end; }
.filter-pill, .style-pill { border: 1px solid var(--feed-line); border-radius: 999px; color: #8e8290; background: #fff; cursor: pointer; transition: .2s ease; }
.filter-pill { padding: 8px 13px; font-size: 12px; }
.filter-pill span { margin-right: 4px; color: #c48a99; }
.filter-pill:hover, .filter-pill.active { border-color: #f5a0ab; color: var(--feed-pink); background: #fff3f5; box-shadow: 0 5px 12px rgba(255, 77, 99, .1); }
.style-filters { margin-bottom: 19px; padding: 12px 15px; border: 1px solid var(--feed-line); border-radius: 17px; background: rgba(255,255,255,.72); }
.style-filter-label { margin-right: 3px; color: #a096a3; font-size: 12px; }
.style-pill { padding: 6px 11px; font-size: 12px; }
.style-pill span { margin-right: 4px; }
.style-pill:hover, .style-pill.active { border-color: #d8cbff; color: #765fc3; background: #f6f2ff; }

.product-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
.product-card { overflow: hidden; border: 1px solid rgba(238, 227, 222, .88); border-radius: 22px; background: rgba(255,255,255,.94); box-shadow: 0 8px 20px rgba(75, 54, 73, .065); cursor: pointer; transition: transform .25s ease, box-shadow .25s ease, border-color .25s ease; }
.product-card:hover, .product-card.visited { border-color: #f6c4c9; box-shadow: 0 16px 30px rgba(113, 76, 104, .13); transform: translateY(-5px); }
.card-image { position: relative; height: 218px; overflow: hidden; background: #fff5ec; }
.card-image img { display: block; width: 100%; height: 100%; object-fit: cover; transition: transform .45s ease; }
.product-card:hover .card-image img { transform: scale(1.045); }
.image-shade { position: absolute; inset: auto 0 0; height: 38%; background: linear-gradient(transparent, rgba(52, 43, 74, .12)); pointer-events: none; }
.rarity-tag, .style-tag { position: absolute; top: 12px; padding: 5px 9px; border-radius: 999px; font-size: 10px; font-weight: 800; }
.rarity-tag { left: 12px; color: #fff; background: #76b79d; }
.rarity-tag.rare-blue { background: #7c95df; }
.rarity-tag.rare-gold { color: #8d5e13; background: #ffe49a; }
.style-tag { right: 12px; color: #fff; background: rgba(52,43,74,.72); backdrop-filter: blur(6px); }
.favorite-button { position: absolute; right: 11px; bottom: 11px; display: grid; width: 34px; height: 34px; place-items: center; border: 1px solid rgba(255,255,255,.86); border-radius: 50%; color: #fff; background: rgba(52,43,74,.5); cursor: pointer; font-size: 20px; line-height: 1; backdrop-filter: blur(6px); transition: .2s ease; }
.favorite-button:hover, .favorite-button.active { color: #fff; background: var(--feed-pink); transform: scale(1.08); }
.card-body { display: flex; min-height: 238px; flex-direction: column; padding: 16px 17px 14px; }
.card-category-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 7px; }
.card-category { color: #a267a0; font-size: 11px; font-weight: 800; }
.card-level { overflow: hidden; color: #b0a6af; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.card-title { display: -webkit-box; overflow: hidden; margin: 0 0 6px; color: var(--feed-plum); font-size: 17px; line-height: 1.42; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.card-subtitle { display: -webkit-box; overflow: hidden; margin: 0 0 7px; color: #756d7c; font-size: 13px; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.card-summary { display: -webkit-box; overflow: hidden; margin: 0 0 9px; color: #a098a5; font-size: 12px; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.card-highlights { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
.card-highlights span { padding: 4px 7px; border-radius: 7px; color: #9b6a31; background: #fff5dc; font-size: 10px; }
.card-meta { display: flex; gap: 10px; margin-top: auto; color: #aaa1ac; font-size: 11px; }
.card-footer { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-top: 10px; }
.price-currency { color: var(--feed-pink); font-size: 14px; font-weight: 800; }
.card-price { color: var(--feed-pink); font-size: 24px; font-weight: 900; letter-spacing: -.04em; }
.view-detail { color: #8a75ce; font-size: 11px; font-weight: 800; white-space: nowrap; }
.view-detail span { font-size: 16px; vertical-align: -1px; }
.card-store { overflow: hidden; margin: 8px 0 0; color: #b0a5b0; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }

.loading-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
.loading-card { overflow: hidden; border: 1px solid var(--feed-line); border-radius: 22px; background: #fff; }
.loading-image { height: 218px; background: #f7eee9; }
.loading-lines { display: grid; gap: 11px; padding: 18px; }
.loading-lines span { display: block; width: 86%; height: 14px; border-radius: 7px; background: #f1e8e4; }
.loading-lines span.short { width: 56%; }
.loading-lines span.price { width: 38%; height: 22px; margin-top: 18px; }
.shimmer { background: linear-gradient(90deg, #f7eee9 25%, #fff8f3 37%, #f7eee9 63%) !important; background-size: 400% 100% !important; animation: shimmer 1.4s ease infinite; }
@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
.feed-result, .feed-empty { margin: 30px 0; padding: 40px 0; border-radius: 22px; background: rgba(255,255,255,.75); }
.feed-empty :deep(.el-empty__description p) { color: var(--feed-muted); }
.pagination { display: flex; justify-content: center; margin-top: 30px; }
.pagination :deep(.el-pagination) { --el-pagination-button-bg-color: #fff; --el-pagination-hover-color: var(--feed-pink); }
.feed-helper { position: fixed; z-index: 10; right: 22px; bottom: 22px; display: flex; align-items: center; gap: 7px; padding: 8px 10px 8px 7px; border: 1px solid #f1dfe1; border-radius: 999px; color: #8c7787; background: rgba(255,255,255,.94); box-shadow: 0 10px 26px rgba(95, 64, 93, .13); font-size: 11px; backdrop-filter: blur(10px); }
.feed-helper strong { color: var(--feed-pink); }
.feed-helper button { padding: 5px 7px; border: 0; border-radius: 999px; color: #fff; background: var(--feed-pink); cursor: pointer; font-size: 10px; font-weight: 800; }

:global(.ai-shopper-dialog.el-dialog) { width: min(520px, calc(100vw - 28px)) !important; overflow: hidden; padding: 0 !important; border: 1px solid #f4dce4; border-radius: 28px; background: #fffafe; box-shadow: 0 26px 70px rgba(75, 48, 86, .2); }
:global(.ai-shopper-dialog .el-dialog__header) { display: none; }
:global(.ai-shopper-dialog .el-dialog__body) { padding: 0; }
:global(.assistant-dialog-content) { color: #342b4a; }
:global(.assistant-dialog-header) { position: relative; display: flex; align-items: center; gap: 13px; padding: 22px 24px 20px; background: linear-gradient(120deg, #fff0f3, #f8f1ff 80%); }
:global(.assistant-dialog-mascot) { display: grid; flex: 0 0 70px; width: 70px; height: 70px; place-items: center; border-radius: 23px; background: rgba(255,255,255,.78); box-shadow: 0 8px 18px rgba(255, 77, 99, .12); }
:global(.assistant-dialog-mascot .jmall-mascot) { filter: drop-shadow(0 6px 5px rgba(198, 87, 118, .17)); }
:global(.assistant-dialog-title) { min-width: 0; }
:global(.assistant-eyebrow) { color: #bb7895; font-size: 10px; font-weight: 800; letter-spacing: .12em; }
:global(.assistant-dialog-title h3) { margin: 4px 0 3px; color: #342b4a; font-size: 22px; letter-spacing: -.04em; }
:global(.assistant-dialog-title p) { margin: 0; color: #95889b; font-size: 12px; line-height: 1.45; }
:global(.assistant-close) { position: absolute; top: 14px; right: 16px; display: grid; width: 28px; height: 28px; place-items: center; border: 0; border-radius: 50%; color: #9c8394; background: rgba(255,255,255,.74); cursor: pointer; font-size: 21px; line-height: 1; transition: .2s ease; }
:global(.assistant-close:hover) { color: #fff; background: #ff6b81; transform: rotate(8deg); }
:global(.assistant-chat) { padding: 18px 24px 16px; }
:global(.assistant-bubble) { display: flex; align-items: center; gap: 8px; padding: 10px 12px; border-radius: 15px 15px 15px 5px; color: #75667e; background: #fff; box-shadow: 0 6px 16px rgba(92, 60, 92, .07); font-size: 12px; line-height: 1.45; }
:global(.assistant-quick-intents) { display: flex; align-items: center; flex-wrap: wrap; gap: 7px; margin-top: 14px; color: #a18d9f; font-size: 11px; }
:global(.assistant-quick-intents button) { padding: 6px 10px; border: 1px solid #f2d7de; border-radius: 999px; color: #a35f78; background: #fff7f8; cursor: pointer; font-size: 11px; transition: .2s ease; }
:global(.assistant-quick-intents button:hover) { border-color: #ff9dae; color: #fff; background: #ff6b81; transform: translateY(-1px); }
:global(.assistant-input-row) { display: flex; gap: 8px; margin-top: 14px; }
:global(.assistant-input) { flex: 1; min-width: 0; }
:global(.assistant-input .el-input__wrapper) { border: 1px solid #f1d9e2; border-radius: 13px; background: #fff; box-shadow: 0 5px 14px rgba(101, 69, 97, .06); }
:global(.assistant-input .el-input__inner) { color: #342b4a; font-size: 12px; }
:global(.assistant-input .el-input__count) { color: #c0aab8; font-size: 9px; }
:global(.assistant-input-row > .el-button) { height: 40px; padding: 0 15px; border: 0; border-radius: 13px; color: #fff; background: #ff5d73; box-shadow: 0 7px 14px rgba(255, 93, 115, .2); font-size: 12px; font-weight: 800; }
:global(.assistant-input-row > .el-button:hover) { background: #f44962; }
:global(.assistant-notice) { margin: 9px 2px 0; color: #9a7b8b; font-size: 11px; line-height: 1.4; }
:global(.assistant-notice.warning) { color: #c47730; }
:global(.assistant-loading) { display: flex; align-items: center; gap: 12px; margin: 0 24px 22px; padding: 15px 17px; border: 1px solid #f1e2f1; border-radius: 17px; background: linear-gradient(110deg, #fff7f8, #f7f3ff); }
:global(.assistant-loading .jmall-mascot) { flex: 0 0 auto; animation: assistant-bob 1.2s ease-in-out infinite; }
:global(.assistant-loading strong), :global(.assistant-loading span) { display: block; }
:global(.assistant-loading strong) { color: #5b476c; font-size: 13px; }
:global(.assistant-loading span) { margin-top: 4px; color: #aa94a9; font-size: 11px; }
:global(.assistant-results) { margin: 0 24px 24px; padding-top: 16px; border-top: 1px dashed #ead7e3; }
:global(.assistant-results-heading) { display: flex; align-items: end; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
:global(.assistant-results-heading h4) { margin: 4px 0 0; color: #49395d; font-size: 15px; }
:global(.assistant-result-count) { padding: 4px 7px; border-radius: 999px; color: #bc7089; background: #fff0f3; font-size: 10px; font-weight: 800; white-space: nowrap; }
:global(.assistant-recommendations) { display: grid; gap: 8px; }
:global(.assistant-product-option) { display: flex; width: 100%; align-items: center; gap: 10px; padding: 8px; border: 1px solid #f0e2e8; border-radius: 15px; color: inherit; background: #fff; cursor: pointer; text-align: left; transition: .2s ease; }
:global(.assistant-product-option:hover) { border-color: #ffacba; background: #fff8fa; box-shadow: 0 8px 17px rgba(255, 93, 115, .1); transform: translateY(-1px); }
:global(.assistant-product-option img) { flex: 0 0 54px; width: 54px; height: 54px; border-radius: 11px; object-fit: cover; background: #fff4ec; }
:global(.assistant-product-copy) { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 3px; }
:global(.assistant-product-copy strong), :global(.assistant-product-copy span) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
:global(.assistant-product-copy strong) { color: #453653; font-size: 12px; }
:global(.assistant-product-copy span) { color: #a18e9f; font-size: 10px; }
:global(.assistant-product-copy b) { color: #ff536b; font-size: 13px; }
:global(.assistant-option-arrow) { padding: 0 5px; color: #9a80d7; font-size: 18px; }
:global(.assistant-no-results) { display: flex; flex-direction: column; align-items: center; padding: 13px 8px 1px; text-align: center; }
:global(.assistant-no-results p) { margin: 7px 0 10px; color: #95889b; font-size: 12px; line-height: 1.5; }
:global(.assistant-no-results button) { padding: 7px 12px; border: 1px solid #f0ccd7; border-radius: 999px; color: #b45f79; background: #fff6f8; cursor: pointer; font-size: 11px; }
@keyframes assistant-bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }

@media (max-width: 1120px) {
  .product-feed { padding-right: 22px; padding-left: 22px; }
  .discovery-hero { padding-right: 40px; padding-left: 44px; }
  .product-grid, .loading-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}

@media (max-width: 820px) {
  .discovery-hero { min-height: 330px; padding: 34px 28px; }
  .hero-copy { max-width: 100%; }
  .hero-mascot { position: absolute; right: 0; bottom: -20px; opacity: .28; transform: scale(.85); transform-origin: bottom right; }
  .mascot-speech { display: none; }
  .mission-card { align-items: flex-start; }
  .mission-mascot { display: none; }
  .feed-toolbar { align-items: flex-start; flex-direction: column; gap: 15px; }
  .feed-filters { justify-content: flex-start; }
  .style-filters { overflow-x: auto; flex-wrap: nowrap; white-space: nowrap; }
  .style-filter-label { flex: 0 0 auto; }
  .product-grid, .loading-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 540px) {
  .product-feed { padding: 14px 14px 72px; }
  .discovery-hero { min-height: 350px; padding: 28px 21px; border-radius: 25px; }
  .hero-copy h1 { font-size: 32px; }
  .hero-copy p { max-width: 250px; font-size: 14px; }
  .hero-search :deep(.el-input-group__append .el-button) { padding: 0 13px; }
  .hero-search :deep(.el-input-group__append .el-button) { font-size: 0; }
  .hero-search :deep(.el-input-group__append .el-button .el-icon) { margin: 0; font-size: 17px; }
  .mission-card { padding: 14px; }
  .mission-icon { flex-basis: 39px; width: 39px; height: 39px; }
  .mission-title-row strong { font-size: 13px; }
  .mission-reward { font-size: 10px; }
  .product-grid, .loading-grid { gap: 12px; }
  .card-image, .loading-image { height: 156px; }
  .card-body { min-height: 220px; padding: 13px 12px 12px; }
  .card-title { font-size: 15px; }
  .card-summary { display: none; }
  .card-price { font-size: 20px; }
  .card-meta { gap: 5px; font-size: 10px; }
  .feed-helper { right: 12px; bottom: 12px; }
  :global(.assistant-dialog-header) { padding: 19px 18px 17px; }
  :global(.assistant-dialog-mascot) { flex-basis: 58px; width: 58px; height: 58px; border-radius: 18px; }
  :global(.assistant-dialog-title h3) { font-size: 19px; }
  :global(.assistant-dialog-title p) { font-size: 11px; }
  :global(.assistant-chat) { padding-right: 18px; padding-left: 18px; }
  :global(.assistant-loading), :global(.assistant-results) { margin-right: 18px; margin-left: 18px; }
  :global(.assistant-input-row) { align-items: stretch; flex-direction: column; }
  :global(.assistant-input-row > .el-button) { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
  .product-card, .card-image img, .progress-track i, .shimmer { transition: none; animation: none; }
}
</style>
