<template>
  <div class="product-editor">
    <div class="editor-header">
      <h2>{{ isEdit ? '编辑商品' : '上架新商品' }}</h2>
      <el-button type="primary" size="large" @click="triggerAgent">
        <el-icon><MagicStick /></el-icon> AI Agent 帮我
      </el-button>
    </div>

    <el-row :gutter="24">
      <!-- Main Editor -->
      <el-col :span="16">
        <el-card shadow="never" class="editor-card">
          <el-form :model="form" label-position="top">
            <el-form-item label="商品名称" required>
              <el-input v-model="form.title" placeholder="如：明前特级西湖龙井 50g" maxlength="120" show-word-limit />
              <el-tag v-if="aiFields.title" size="small" type="warning" effect="plain" class="ai-badge">🤖 AI 建议</el-tag>
            </el-form-item>
            <el-form-item label="商品副标题">
              <el-input v-model="form.subtitle" placeholder="AI 可生成，发布前可继续修改" maxlength="160" show-word-limit />
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="品类" required>
                  <el-select v-model="form.category" placeholder="选择品类" filterable allow-create>
                    <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="基础价格 (元)" required>
                  <el-input-number v-model="form.priceYuan" :min="0.01" :step="0.01" :precision="2" style="width: 100%" placeholder="请输入真实价格" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- Product Image Area -->
            <el-form-item label="商品图片">
              <div class="image-area">
                <div class="image-list">
                  <div v-for="(url, index) in form.images" :key="index" class="image-item">
                    <img :src="url" class="uploaded-image" />
                    <div class="image-actions">
                      <el-button circle size="small" type="danger" @click="removeImage(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                  <!-- AI Generated Image Preview -->
                  <div v-if="generatedImage && form.images.length === 0" class="image-item generated">
                    <img :src="generatedImage" class="uploaded-image" />
                    <div class="image-actions">
                      <el-button circle size="small" type="success" @click="useGeneratedImage">使用</el-button>
                    </div>
                    <div class="generated-label">🤖 AI 生成</div>
                  </div>
                  <!-- Category Fallback Image -->
                  <div v-if="!generatedImage && form.images.length === 0" class="image-item fallback">
                    <img :src="categoryPlaceholder" class="uploaded-image" />
                    <div class="generated-label">📷 示例图</div>
                  </div>
                  <el-upload
                    v-if="form.images.length < 6"
                    :action="uploadUrl"
                    :headers="uploadHeaders"
                    :show-file-list="false"
                    :before-upload="beforeImageUpload"
                    :on-success="onImageSuccess"
                    :on-error="onImageError"
                    accept="image/*"
                    class="image-upload-trigger"
                  >
                    <div class="upload-placeholder">
                      <el-icon :size="24"><Plus /></el-icon>
                      <span>{{ form.images.length === 0 ? '上传图片' : '添加' }}</span>
                    </div>
                  </el-upload>
                </div>
                <p class="upload-hint">支持 JPG/PNG/WebP，单张不超过 5MB，最多 6 张。未上传时将根据品类自动生成示例图</p>
              </div>
            </el-form-item>

            <el-form-item label="商品详情（AI 将生成结构化详情页文案）">
              <el-input v-model="form.description" type="textarea" :rows="12" placeholder="AI 将根据商品事实生成商品概览、核心亮点、规格参数、适用场景与购买提示" maxlength="5000" show-word-limit />
              <el-tag v-if="aiFields.description" size="small" type="warning" effect="plain" class="ai-badge">🤖 AI 建议</el-tag>
            </el-form-item>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="规格参数">
                  <el-input v-model="form.specifications" type="textarea" :rows="3" placeholder="每行一项，AI 建议需商家核实" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="目标人群">
                  <el-input v-model="form.targetAudience" type="textarea" :rows="3" placeholder="填写可核验的适用人群" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="使用场景">
                  <el-input v-model="form.usageScenarios" placeholder="多个场景用逗号分隔" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="SEO 关键词">
                  <el-input v-model="form.seoKeywords" placeholder="多个关键词用逗号分隔" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="促销文案">
              <el-input v-model="form.promotionCopy" type="textarea" :rows="2" placeholder="不确定的优惠信息请勿发布" />
            </el-form-item>
            <el-form-item v-if="aiPriceSuggestionYuan !== null" label="AI 价格建议（仅供参考）">
              <div class="price-suggestion">
                <strong>¥{{ aiPriceSuggestionYuan.toFixed(2) }}</strong>
                <el-button size="small" plain @click="form.priceYuan = aiPriceSuggestionYuan">应用建议</el-button>
              </div>
            </el-form-item>
            <el-form-item label="展示风格">
              <el-select v-model="form.style">
                <el-option v-for="s in styles" :key="s.value" :label="s.label" :value="s.value">
                  {{ s.icon }} {{ s.label }}
                </el-option>
              </el-select>
            </el-form-item>
            <!-- AI Selling Points -->
            <el-form-item v-if="aiFields.sellingPoints.length > 0" label="AI 卖点建议">
              <div class="ai-selling-points">
                <el-tag v-for="(point, i) in aiFields.sellingPoints" :key="i" effect="plain" class="selling-point-tag">
                  ✨ {{ point }}
                </el-tag>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="success" size="large" @click="saveProduct" :loading="saving">
                {{ isEdit ? '保存修改' : '发布商品' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Agent Panel (Right Sidebar) -->
      <el-col :span="8">
        <div class="agent-panel" v-if="agentActive">
          <el-card shadow="never">
            <template #header>
              <div class="agent-panel-header">
                <span>🤖 Agent 参谋团</span>
                <el-switch v-model="agentActive" size="small" />
              </div>
            </template>

            <!-- Demo Mode Banner -->
            <el-alert
              v-if="agentDemoMode"
              title="当前为安全降级模板（非实时数据）"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 16px;"
            />

            <!-- Agent Progress Checklist -->
            <div v-if="agentLoading || Object.keys(agentStages).length > 0" class="agent-checklist">
              <div
                v-for="stage in stageList"
                :key="stage.key"
                class="checklist-item"
                :class="agentStages[stage.key] || 'pending'"
              >
                <el-icon v-if="agentStages[stage.key] === 'completed'" class="check-icon done"><CircleCheck /></el-icon>
                <el-icon v-else-if="agentStages[stage.key] === 'running'" class="check-icon running is-loading"><Loading /></el-icon>
                <el-icon v-else-if="agentStages[stage.key] === 'error'" class="check-icon error"><CircleClose /></el-icon>
                <el-icon v-else class="check-icon pending"><Clock /></el-icon>
                <span class="checklist-label">{{ stage.label }}</span>
                <span v-if="stageDetail(stage.key)" class="stage-detail">{{ stageDetail(stage.key) }}</span>
              </div>
            </div>

            <!-- RAG Quality Metrics -->
            <div v-if="ragQuality" class="agent-section rag-quality">
              <h4>📊 知识库检索质量</h4>
              <div class="quality-bar">
                <div class="quality-level" :class="ragQuality.quality">
                  {{ { excellent: '优秀', good: '良好', fair: '一般', poor: '较差', empty: '未检索' }[ragQuality.quality] || ragQuality.quality }}
                </div>
                <div class="quality-metrics">
                  <span>结果数: {{ ragQuality.result_count ?? 0 }}</span>
                  <span v-if="ragQuality.top1_score > 0">最高相似度: {{ (ragQuality.top1_score * 100).toFixed(1) }}%</span>
                  <span v-if="ragQuality.avg_score > 0">平均相似度: {{ (ragQuality.avg_score * 100).toFixed(1) }}%</span>
                </div>
              </div>
            </div>

            <!-- Market Insights -->
            <div v-if="marketInsights" class="agent-section">
              <h4>📈 市场趋势</h4>
              <div class="trend-tags">
                <el-tag v-for="(t, i) in (marketInsights.trends || [marketInsights.trends_summary])" :key="i" size="small" type="warning">{{ t }}</el-tag>
              </div>
              <div class="hot-keywords" v-if="marketInsights.hotKeywords?.length">
                <span>热搜词：</span>
                <el-tag v-for="k in marketInsights.hotKeywords" :key="k" size="small" effect="plain">{{ k }}</el-tag>
              </div>
              <p class="price-range" v-if="marketInsights.priceRange">
                同类定价区间：{{ formatPriceYuan(marketInsights.priceRange.low || marketInsights.priceRange.min || 0) }} - {{ formatPriceYuan(marketInsights.priceRange.high || marketInsights.priceRange.max || 0) }} 元
              </p>
              <div v-if="marketInsights.suggestions?.length" class="market-suggestions">
                <p v-for="(s, i) in marketInsights.suggestions" :key="i">💡 {{ s }}</p>
              </div>
              <div class="market-provenance">
                <span>调研范围：{{ marketInsights.researchScope || '公开互联网实时检索' }}</span>
                <span v-if="marketInsights.searchProvider">检索服务：{{ getSearchProviderLabel(marketInsights.searchProvider) }}</span>
              </div>
              <div v-if="marketInsights.sources?.length" class="market-sources">
                <strong>参考来源（{{ marketInsights.sources.length }}）</strong>
                <a
                  v-for="(source, i) in marketInsights.sources"
                  :key="source.url || i"
                  :href="source.url"
                  target="_blank"
                  rel="noopener noreferrer"
                >{{ Number(i) + 1 }}. {{ source.title || source.url }}</a>
              </div>
              <el-alert
                v-else
                title="本次检索没有返回可展示的来源链接，请将趋势结论仅作参考。"
                type="warning"
                :closable="false"
                show-icon
                class="market-source-warning"
              />
            </div>

            <!-- Copy Previews per Platform (Visual Cards) -->
            <div v-if="availablePreviewStyles.length > 0" class="agent-section">
              <h4>✍️ {{ getSelectedStyleName() }}文案</h4>
              <div class="style-cards">
                <div
                  v-for="s in availablePreviewStyles"
                  :key="s.value"
                  class="style-card"
                  :class="{ active: true }"
                >
                  <div class="style-card-bar" :style="{ background: getStyleColor(s.value) }">
                    <span class="style-card-platform">{{ s.icon }} {{ getStyleLabel(s.value) }}</span>
                  </div>
                  <div class="style-card-body">
                    <div class="style-card-title">
                      {{ stylePreviews[s.value]?.adapted_title || stylePreviews[s.value]?.title || '点击生成...' }}
                    </div>
                    <ul class="style-card-points">
                      <li v-for="(point, i) in getPublishableSellingPoints(stylePreviews[s.value], agentFullData?.copy)" :key="i">
                        {{ point }}
                      </li>
                    </ul>
                    <div v-if="buildPublishableDetail(stylePreviews[s.value], agentFullData?.copy)" class="style-card-detail">
                      {{ buildPublishableDetail(stylePreviews[s.value], agentFullData?.copy).slice(0, 120) }}...
                    </div>
                  </div>
                  <div class="style-card-footer">
                    <el-button size="small" type="primary" plain @click.stop="applyStylePreview(s.value)">
                      应用{{ getSelectedStyleName() }}文案
                    </el-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Compliance Check -->
            <div v-if="complianceResult" class="agent-section" :class="complianceResult.passed ? 'compliance-pass' : 'compliance-fail'">
              <h4>⚖️ 合规审查</h4>
              <div v-if="complianceResult.passed">
                <el-tag type="success">✅ {{ complianceResult.summary || '审查通过' }}</el-tag>
              </div>
              <div v-else>
                <el-tag type="danger" v-for="e in (complianceResult.errors || complianceResult.issues || [])" :key="e" style="margin: 2px">{{ e }}</el-tag>
                <el-tag type="warning" v-for="w in (complianceResult.warnings || [])" :key="w" style="margin: 2px">{{ w }}</el-tag>
              </div>
            </div>

            <!-- Agent Completion Summary -->
            <div v-if="agentComplete" class="agent-section agent-complete">
              <h4>{{ agentHadErrors ? '⚠️ Agent 降级完成' : '✅ Agent 任务完成' }}</h4>
              <p class="complete-summary">{{ agentCompleteSummary }}</p>
              <div v-if="agentCostStats" class="cost-stats">
                <el-tag size="small" type="info">{{ agentCostStats }}</el-tag>
                <details v-if="agentTokenBreakdown.length" class="cost-breakdown">
                  <summary>Token 去向</summary>
                  <div v-for="item in agentTokenBreakdown" :key="item.agent" class="cost-row">
                    <span>{{ getAgentLabel(item.agent) }}</span>
                    <span>{{ item.total_tokens.toLocaleString() }} Token · ${{ Number(item.cost_usd || 0).toFixed(6) }}</span>
                  </div>
                </details>
              </div>
            </div>
          </el-card>
        </div>

        <!-- Agent Toggle (when closed) -->
        <div v-else class="agent-collapsed" @click="agentActive = true">
          <el-icon><MagicStick /></el-icon>
          <span>AI 参谋团</span>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { productApi } from '@/services/products'
import { useAuthStore } from '@/stores/auth'
import type { PlatformStyle } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const agentActive = ref(true)
const agentLoading = ref(false)
const agentStatus = ref('')
const agentDemoMode = ref(false)
const agentComplete = ref(false)
const agentCompleteSummary = ref('')
const agentCostStats = ref('')
const agentTokenBreakdown = ref<Array<{ agent: string; total_tokens: number; cost_usd: number }>>([])
// Agent stage tracking for SSE progress checklist
const agentStages = ref<Record<string, 'pending' | 'running' | 'completed' | 'error'>>({})
const agentErrors = ref<Record<string, string>>({})
const ragQuality = ref<any>(null)
const marketResearchDetail = ref('')
const ragDetail = ref('')
const copyDetail = ref('')
const currentJobId = ref<string | null>(null)  // Persistent job ID for reconnection
const JOB_STORAGE_KEY = 'jmall-agent-job'
const JOB_CONSUMED_KEY = 'jmall-agent-consumed-job'

const stageList = [
  { key: 'parse_intent', label: '🧠 解析意图' },
  { key: 'market_research', label: '🔍 市场调研' },
  { key: 'rag_retrieval', label: '📚 知识库检索' },
  { key: 'copy_generation', label: '✍️ 文案生成' },
  { key: 'compliance_review', label: '⚖️ 合规审查' },
  { key: 'style_adaptation', label: '🎨 风格适配' },
]

const agentHadErrors = computed(() => Object.values(agentStages.value).includes('error'))

function stageDetail(key: string): string {
  if (agentStages.value[key] === 'error') return agentErrors.value[key] || '该步骤已降级'
  if (agentStages.value[key] !== 'completed') return ''
  switch (key) {
    case 'market_research': return marketResearchDetail.value
    case 'rag_retrieval': return ragDetail.value
    case 'copy_generation': return copyDetail.value
    default: return ''
  }
}

const categories = ['食品饮料', '生鲜水果', '服饰鞋包', '家居日用', '数码家电', '美妆护肤', '运动户外', '图书文娱', '其他']
const styles = [
  { value: 'pinduoduo', label: '拼多多风', icon: '🔴' },
  { value: 'taobao', label: '淘宝风', icon: '🟠' },
  { value: 'jd', label: '京东风', icon: '🔴' },
  { value: 'suning', label: '苏宁风', icon: '🔵' },
  { value: 'xiaohongshu', label: '小红书风', icon: '💗' },
]
const availablePreviewStyles = computed(() => {
  const selected = styles.find(s => s.value === form.style)
  return selected && stylePreviews.value[selected.value] ? [selected] : []
})

function getSelectedStyleName(): string {
  return styles.find(s => s.value === form.style)?.label || '所选风格'
}

function getSearchProviderLabel(provider: string): string {
  const labels: Record<string, string> = {
    qwen_web_search: '阿里云百炼 Qwen 联网搜索',
    realtime_search_with_fallback: 'Tavily（失败时自动切换 Qwen）',
    tavily_search_results_json: 'Tavily',
  }
  return labels[provider] || provider
}

function getAgentLabel(agent: string): string {
  const labels: Record<string, string> = {
    orchestration: '任务编排',
    market_research: '市场分析',
    'market_research.web_search': '联网搜索',
    copy_generation: '商品文案',
    compliance_review: '合规审查',
    style_adaptation: '所选平台风格',
  }
  return labels[agent] || agent
}

function applyCostStats(costStats: any) {
  if (!costStats) return
  const tokens = Number(costStats.total_tokens ?? costStats.tokens ?? 0)
  const cost = Number(costStats.total_cost_usd ?? costStats.total_cost ?? costStats.cost ?? 0)
  if (tokens > 0) {
    agentCostStats.value = `Token: ${tokens.toLocaleString()} | 预估成本: $${cost.toFixed(6)}`
  }
  const breakdown = costStats.tokens_by_agent || {}
  agentTokenBreakdown.value = Object.entries(breakdown)
    .map(([agent, value]: [string, any]) => ({
      agent,
      total_tokens: Number(value?.total_tokens || 0),
      cost_usd: Number(value?.cost_usd || 0),
    }))
    .filter(item => item.total_tokens > 0)
    .sort((a, b) => b.total_tokens - a.total_tokens)
}

function mapMarketInsights(mi: any) {
  return {
    trends: mi.trends_summary ? [mi.trends_summary] : (Array.isArray(mi.trends) ? mi.trends : (mi.trends ? [mi.trends] : [])),
    trends_summary: mi.trends_summary || mi.trends,
    hotKeywords: mi.hot_keywords || mi.keywords || [],
    priceRange: mi.status === 'failed' ? null : (mi.price_range || mi.competitor_price_range || null),
    suggestions: mi.suggestions || [],
    sources: mi.sources || [],
    searchProvider: mi.search_provider || mi.search_tool || '',
    researchScope: mi.research_scope || '',
    method: mi.method || '',
  }
}

function mergeStylePreviews(sp: any) {
  if (!sp) return
  const allPreviews = sp.previews || sp.platform_previews
  if (allPreviews && typeof allPreviews === 'object') {
    stylePreviews.value = { ...stylePreviews.value, ...allPreviews }
  }
  if (sp.adapted_title || sp.titles?.[0] || sp.adapted_selling_points || sp.selling_points) {
    const styleKey = sp.target_style || sp.style || form.style
    stylePreviews.value = {
      ...stylePreviews.value,
      [styleKey]: {
        ...stylePreviews.value[styleKey],
        adapted_title: sp.adapted_title || sp.titles?.[0] || form.title,
        adapted_selling_points: sp.adapted_selling_points || sp.selling_points || [],
        adapted_detail: sp.adapted_detail || sp.detail_copy || form.description,
      },
    }
  }
}

const form = reactive({
  title: '',
  subtitle: '',
  category: '',
  description: '',
  priceYuan: 0,
  specifications: '',
  targetAudience: '',
  usageScenarios: '',
  seoKeywords: '',
  promotionCopy: '',
  style: 'taobao' as PlatformStyle,
  images: [] as string[],
})

const aiFields = reactive({
  title: false,
  description: false,
  style: false,
  sellingPoints: [] as string[],
  aiTitle: '',
  aiSellingPoints: '' as string,
  aiDetail: '',
  aiStylePreviews: '' as string,
  marketInsights: '' as string,
  complianceResult: '' as string,
})

const marketInsights = ref<any>(null)
const stylePreviews = ref<Record<string, any>>({})
const complianceResult = ref<any>(null)
const agentFullData = ref<any>(null)
const aiPriceSuggestionYuan = ref<number | null>(null)
const knowledgeBaseId = ref('')
const generatedImage = ref('')
const imageGenFailed = ref(false)

// Image upload
const uploadUrl = '/api/upload/image'
const uploadHeaders = computed(() => {
  const h: Record<string, string> = {}
  if (authStore.token) h.Authorization = `Bearer ${authStore.token}`
  return h
})

// ===== Image Generation =====
const CATEGORY_IMAGES: Record<string, string> = {
  '食品饮料': 'https://placehold.co/400x400/fff3e0/ff9800?text=🍪+食品饮料',
  '生鲜水果': 'https://placehold.co/400x400/e8f5e9/4caf50?text=🍎+生鲜水果',
  '服饰鞋包': 'https://placehold.co/400x400/fce4ec/e91e63?text=👗+服饰鞋包',
  '家居日用': 'https://placehold.co/400x400/fff8e1/fbc02d?text=🏠+家居日用',
  '数码家电': 'https://placehold.co/400x400/e3f2fd/2196f3?text=📱+数码家电',
  '美妆护肤': 'https://placehold.co/400x400/f3e5f5/9c27b0?text=💄+美妆护肤',
  '运动户外': 'https://placehold.co/400x400/e8eaf6/3f51b5?text=⚽+运动',
  '图书文娱': 'https://placehold.co/400x400/efebe9/795548?text=📚+图书',
}

const categoryPlaceholder = computed(() => {
  return CATEGORY_IMAGES[form.category] || 'https://placehold.co/400x400/e8e8e8/999?text=📦+商品'
})

async function tryGenerateImage() {
  if (form.images.length > 0 || !form.title) return
  imageGenFailed.value = false
  try {
    const resp = await fetch('/api/ai/product/copy', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('jmall-token')}`,
      },
      body: JSON.stringify({
        productInfo: { title: form.title, category: form.category || '其他', description: form.description, price: form.priceYuan },
        targetStyle: form.style,
      }),
    })
    if (resp.ok) {
      const data = await resp.json()
      // Check if we got an image URL back
      const imgUrl = data?.data?.image_url || data?.image_url
      if (imgUrl) {
        generatedImage.value = imgUrl
      }
    }
  } catch {
    imageGenFailed.value = true
  }
}

function useGeneratedImage() {
  if (generatedImage.value) {
    form.images = [generatedImage.value]
    generatedImage.value = ''
    ElMessage.success('已使用 AI 生成图片')
  }
}

// ===== Platform-specific safe fallback =====
// Only reshapes merchant-provided facts. It deliberately avoids invented
// sales, prices, certifications, ingredients, discounts, or realtime trends.
const PLATFORM_DATA: Record<string, any> = {
  pinduoduo: {
    titlePrefix: '【好物推荐】',
    selling_points: ['名称直观，核心信息前置', '表达简洁，便于快速浏览', '价格与优惠请按实际信息补充'],
    styleNote: '拼多多风安全模板：突出性价比表达，不添加未经确认的折扣与销量。',
  },
  taobao: {
    titlePrefix: '【商品推荐】',
    selling_points: ['标题包含商品名与品类', '详情按特点和使用场景分层', '补充真实规格有助于搜索与决策'],
    styleNote: '淘宝风安全模板：强调信息完整与搜索友好。',
  },
  jd: {
    titlePrefix: '【规格清晰】',
    selling_points: ['商品信息规范展示', '建议补充可核验的规格参数', '认证、物流与售后仅填写真实承诺'],
    styleNote: '京东风安全模板：参数导向，不虚构认证与服务。',
  },
  suning: {
    titlePrefix: '【品质商品】',
    selling_points: ['突出品类与核心用途', '建议补充真实参数和适用场景', '服务与保障以商家实际政策为准'],
    styleNote: '苏宁风安全模板：参数与服务并重，不添加未确认权益。',
  },
  xiaohongshu: {
    titlePrefix: '✨ 使用灵感｜',
    selling_points: ['从真实使用场景切入', '语气自然，避免虚构亲身体验', '功效与数据需要可核验依据'],
    styleNote: '小红书风安全模板：场景化表达，不伪造体验与功效。',
  },
}

function getPlatformDemoData(style: string) {
  return PLATFORM_DATA[style] || PLATFORM_DATA.taobao
}

// ===== Style helpers =====
const styleColorMap: Record<string, string> = {
  pinduoduo: 'linear-gradient(135deg, #e02e24, #f04e23)',
  taobao: 'linear-gradient(135deg, #ff5000, #ff6c38)',
  jd: 'linear-gradient(135deg, #c91623, #e3333f)',
  suning: 'linear-gradient(135deg, #ffc000, #f5a623)',
  xiaohongshu: 'linear-gradient(135deg, #fe2c55, #ff4d7a)',
}

const styleLabelMap: Record<string, string> = {
  pinduoduo: '拼多多风 — 价格驱动', taobao: '淘宝风 — 搜索驱动', jd: '京东风 — 品质驱动',
  suning: '苏宁风 — 家电参数风', xiaohongshu: '小红书风 — 种草口吻',
}

function getStyleColor(style: string) { return styleColorMap[style] || '#409eff' }
function getStyleLabel(style: string) { return styleLabelMap[style] || style }

function formatPriceYuan(yuan: number) {
  return Number(yuan || 0).toFixed(2)
}

// ===== AI Agent Orchestration =====
async function triggerAgent() {
  if (!form.title) {
    ElMessage.warning('请先填写商品名称')
    return
  }
  if (!form.category) {
    ElMessage.warning('请选择商品分类')
    return
  }
  agentActive.value = true
  agentLoading.value = true
  agentDemoMode.value = false
  agentComplete.value = false
  agentCompleteSummary.value = ''
  agentCostStats.value = ''
  agentTokenBreakdown.value = []
  agentStatus.value = '🤖 Agent 团队正在启动...'

  // Reset
  marketInsights.value = null
  stylePreviews.value = {}
  complianceResult.value = null
  agentFullData.value = null
  generatedImage.value = ''
  ragQuality.value = null
  marketResearchDetail.value = ''
  ragDetail.value = ''
  copyDetail.value = ''
  agentErrors.value = {}

  // Initialize all stages as pending
  for (const stage of stageList) {
    agentStages.value[stage.key] = 'pending'
  }
  agentStages.value['parse_intent'] = 'running'

  try {
    const response = await fetch('/api/ai/orchestrate/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('jmall-token')}`,
      },
      body: JSON.stringify({
        productInfo: {
          title: form.title,
          category: form.category || '其他',
          description: form.description,
          price: form.priceYuan,
          specifications: form.specifications,
          target_audience: form.targetAudience,
          usage_scenarios: form.usageScenarios,
        },
        targetStyle: form.style,
        knowledgeBaseId: knowledgeBaseId.value || undefined,
        productDraftId: isEdit.value ? Number(route.params.id) : undefined,
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''
    let eventName = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        const normalizedLine = line.endsWith('\r') ? line.slice(0, -1) : line
        if (normalizedLine.startsWith('event:')) {
          eventName = normalizedLine.slice(6).trim()
        } else if (normalizedLine.startsWith('data:')) {
          try {
            const data = JSON.parse(normalizedLine.slice(5).trimStart())

            // Capture jobId for reconnection
            if (eventName === 'job_created') {
              currentJobId.value = data.jobId
              if (currentJobId.value) {
                localStorage.setItem(JOB_STORAGE_KEY, currentJobId.value)
              }
              continue
            }

            if (eventName === 'agent_progress' || !eventName) {
              const agent = data.agent

              // Mark completed stage
              if (agent && agentStages.value[agent] !== undefined) {
                agentStages.value[agent] = data.status === 'error' ? 'error' : 'completed'
                if (data.status === 'error') {
                  agentErrors.value[agent] = data.error
                    || data.plan?.error
                    || data.market_insights?.error
                    || data.style_previews?.error
                    || data.compliance_result?.error
                    || '服务不可用，已使用安全降级结果'
                }
              }
              // Mark next stage as running
              markNextRunning()

              // Market insights
              if (data.market_insights) {
                const mi = data.market_insights
                marketInsights.value = mapMarketInsights(mi)
                const kc = (mi.hot_keywords || mi.keywords || []).length
                const tc = (mi.trends || []).length
                marketResearchDetail.value = `${tc}条趋势, ${kc}个热搜词`
                if (mi.method) marketResearchDetail.value += ` (${mi.method})`
              }

              // RAG quality
              if (data.rag_quality) {
                ragQuality.value = data.rag_quality
                const rq = data.rag_quality
                ragDetail.value = `${rq.result_count ?? 0}条结果`
                if (rq.quality) ragDetail.value += `, 质量: ${rq.quality}`
              }
              if (data.rag_context) {
                const rc = data.rag_context
                const count = rc.chunk_count || 0
                ragDetail.value = `${count}条结果`
              }

              // Copy/style previews
              if (data.style_previews || data.copy) {
                const sp = data.style_previews || data.copy
                mergeStylePreviews(sp)
                const ptCount = (sp.adapted_selling_points || sp.selling_points || []).length
                copyDetail.value = ptCount > 0 ? `${ptCount}个卖点` : ''
              }

              // Compliance
              if (data.compliance_result || data.compliance) {
                const cr = data.compliance_result || data.compliance
                complianceResult.value = {
                  passed: cr.status === 'passed',
                  warnings: cr.warnings || [],
                  errors: cr.issues || [],
                  summary: cr.summary || '',
                  checklist: cr.checklist || {},
                }
              }
            }

            if (eventName === 'done') {
              // Keep the completed job ID until the generated form is published.
              // A refresh or route change can still restore its persisted result.
            }

            if (eventName === 'orchestration_complete') {
              agentStatus.value = '✅ Agent 团队完成任务!'
              agentFullData.value = data.final_result || data

              // Mark all pending stages as completed
              for (const stage of stageList) {
                if (agentStages.value[stage.key] === 'pending' || agentStages.value[stage.key] === 'running') {
                  agentStages.value[stage.key] = 'completed'
                }
              }

              // Completion summary
              const fr = data.final_result || data
              const status = fr?.overall_status || 'success'
              const statusMap: Record<string, string> = {
                success: '所有Agent任务已成功完成，表单已自动填充',
                ready_with_warnings: 'Agent任务完成（有轻微警告），请检查后发布',
                needs_revision: 'Agent任务完成，建议修改后再发布',
                partial_success: '部分Agent任务完成，表单已填充可用内容',
              }
              agentCompleteSummary.value = statusMap[status] || 'Agent任务已完成'
              agentComplete.value = true

              // Cost stats
              if (data.cost_stats) {
                applyCostStats(data.cost_stats)
              }

              // Auto-fill from final result
              if (fr?.style_adaptation?.target_style) {
                form.style = fr.style_adaptation.target_style
              }
              if (fr?.copy) {
                const copy = fr.copy
                if (copy.adapted_title || (copy.titles?.[0])) {
                  const bestTitle = copy.adapted_title || copy.titles[0]
                  form.title = bestTitle
                  aiFields.title = true
                  aiFields.aiTitle = bestTitle
                }
                const points = copy.adapted_selling_points || copy.selling_points || []
                if (points.length > 0) {
                  const publishablePoints = getPublishableSellingPoints(copy, copy)
                  aiFields.sellingPoints = publishablePoints
                  aiFields.aiSellingPoints = JSON.stringify(publishablePoints)
                }
                fillExtendedCopy(copy)
                const selectedPreview = selectedPreviewFromResult(fr, copy)
                mergeConfirmationItemsIntoSpecifications(copy, String(selectedPreview?.adapted_detail || selectedPreview?.detail || ''))
                applyGeneratedDescription(selectedPreview, copy)
              }
              if (fr?.market_insights) {
                marketInsights.value = mapMarketInsights(fr.market_insights)
                aiFields.marketInsights = JSON.stringify(fr.market_insights)
              }
              if (fr?.compliance) {
                aiFields.complianceResult = JSON.stringify(fr.compliance)
              }
              if (fr?.style_adaptation) {
                mergeStylePreviews(fr.style_adaptation)
                aiFields.aiStylePreviews = JSON.stringify(fr.style_adaptation)
                if (fr.style_adaptation.target_style) {
                  form.style = fr.style_adaptation.target_style
                  aiFields.style = true
                }
              }

              if (status === 'partial_success' || status === 'needs_revision') {
                ElMessage.warning('AI 已降级完成，请核实标红步骤与待确认内容后发布')
              } else {
                ElMessage.success('✅ AI 已自动填充表单，可手动调整后发布')
              }
            }

            if (eventName === 'error') {
              console.error('Agent SSE error:', data.error)
              // Mark current running stage as error
              for (const stage of stageList) {
                if (agentStages.value[stage.key] === 'running') {
                  agentStages.value[stage.key] = 'error'
                  break
                }
              }
            }
          } catch { /* skip unparseable */ }
          eventName = ''
        }
      }
    }
    agentLoading.value = false
  } catch (e: any) {
    agentLoading.value = false
    // If we have a jobId, the job is still running on server — don't clear state
    if (currentJobId.value) {
      console.log('Agent SSE disconnected, job still running:', currentJobId.value)
      // Mark running stage as pending (not error) — it's still running server-side
      for (const stage of stageList) {
        if (agentStages.value[stage.key] === 'running') {
          agentStages.value[stage.key] = 'pending'
        }
      }
      ElMessage.info('Agent 任务仍在后台运行，刷新页面后可查看进度')
      return  // Don't load demo data — real data may arrive
    }
    // Mark running stage as error only if no jobId (complete failure)
    for (const stage of stageList) {
      if (agentStages.value[stage.key] === 'running') {
        agentStages.value[stage.key] = 'error'
      }
    }
    // Load a clearly-labelled safe fallback based only on submitted facts.
    loadPlatformDemoData()
    agentDemoMode.value = true
    ElMessage.warning('Agent 服务暂时不可用，已加载安全降级模板（不含实时市场数据）')
  }
}

function markNextRunning() {
  for (const stage of stageList) {
    if (agentStages.value[stage.key] === 'pending') {
      agentStages.value[stage.key] = 'running'
      break
    }
  }
}

function loadPlatformDemoData() {
  const category = form.category || '食品饮料'

  // Mark all stages as completed for demo mode
  for (const stage of stageList) {
    agentStages.value[stage.key] = 'completed'
  }
  marketResearchDetail.value = '实时调研不可用'
  ragDetail.value = '未使用知识库结果'
  copyDetail.value = '3个安全提示'
  agentComplete.value = true
  agentCompleteSummary.value = '已加载安全降级模板，请核实并完善商品事实'

  // Explicitly report absence of realtime market evidence.
  marketInsights.value = {
    trends: ['实时市场调研暂时不可用，未生成趋势结论'],
    trends_summary: `${category}品类暂无可核验的实时市场结果`,
    hotKeywords: [],
    priceRange: null,
    suggestions: ['可先完善商品真实规格、适用场景与售后信息，稍后重试'],
  }

  // Platform-specific style previews
  const previews: Record<string, any> = {}
  const merchantHighlights = form.description
    .split(/[\n。；;]+/)
    .map(item => item.trim())
    .filter(item => item && !isMerchantConfirmation(item))
    .slice(0, 5)
  for (const s of ['pinduoduo', 'taobao', 'jd', 'suning', 'xiaohongshu']) {
    const pd = getPlatformDemoData(s)
    const title = `${pd.titlePrefix}${form.title || '商品'}`
    const points = merchantHighlights.length > 0 ? merchantHighlights : pd.selling_points
    const detail = form.description || `请补充「${form.title || '商品'}」的真实规格、特点、使用场景与售后信息。`
    previews[s] = {
      adapted_title: title,
      adapted_selling_points: points,
      adapted_detail: detail,
      style_notes: pd.styleNote,
    }
  }
  stylePreviews.value = previews

  // Compliance
  complianceResult.value = {
    passed: false,
    warnings: ['模型合规审查未执行，发布前必须人工核实'],
    errors: [],
    summary: '降级模式未执行模型合规审查，请人工核实全部商品描述后再发布。',
    checklist: { manual_review_required: true },
  }

  // Full data
  agentFullData.value = {
    product_title: form.title,
    copy: {
      titles: previews[form.style]?.adapted_title ? [previews[form.style].adapted_title] : [form.title],
      selling_points: previews[form.style]?.adapted_selling_points || [],
      detail_copy: previews[form.style]?.adapted_detail || form.description,
      subtitle: `${category}商品信息待完善`,
      price_suggestion: null,
      specifications: ['请补充可核验规格'],
      target_audience: '请根据真实适用范围补充',
      usage_scenarios: ['请根据真实用途补充'],
      seo_keywords: [form.title, category].filter(Boolean),
      promotion_copy: `${previews[form.style]?.adapted_title || form.title}，价格与优惠以商家实际设置为准。`,
    },
    style_adaptation: { target_style: form.style, style_notes: getStyleLabel(form.style) },
    overall_status: 'needs_revision',
  }
  fillExtendedCopy(agentFullData.value.copy)
}

function asTextList(value: unknown): string {
  return toTextItems(value).join('，')
}

function toTextItems(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.flatMap(item => toTextItems(item))
  }
  if (value && typeof value === 'object') {
    const item = value as Record<string, unknown>
    return toTextItems(
      item.adapted_selling_point
      || item.selling_point
      || item.text
      || item.value
      || item.name,
    )
  }
  if (typeof value !== 'string') return []
  return value
    .split(/[\n；;]+/)
    .map(item => item.replace(/^[\s•·*-]+/, '').trim())
    .filter(Boolean)
}

function isMerchantConfirmation(text: string): boolean {
  return /请(?:商家|根据|补充|确认|核实|勿)|待(?:商家)?确认|未确认|购买前(?:请)?核对|可核验|核验商品|信息待完善|不确定|以.+为准|不作.+承诺|仅围绕商家已确认/.test(text)
}

function uniqueTextItems(...values: unknown[]): string[] {
  return Array.from(new Set(values.flatMap(value => toTextItems(value))))
}

function extractDetailSection(detail: string, heading: string): string {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return detail.match(new RegExp(`【${escaped}】\\s*([\\s\\S]*?)(?=【[^】]+】|$)`))?.[1]?.trim() || ''
}

function cleanPublishableBlock(value: string): string {
  return value
    .split(/\n+|(?<=[。！？；;])/)
    .map(line => line.replace(/^重点先看[:：]?\s*/, '').trim())
    .filter(line => line && !isMerchantConfirmation(line))
    .join('\n')
}

function getPublishableSellingPoints(preview: any, copy?: any): string[] {
  const candidates = preview?.adapted_selling_points
    || preview?.selling_points
    || preview?.sellingPoints
    || copy?.adapted_selling_points
    || copy?.selling_points
    || []
  return uniqueTextItems(candidates).filter(item => !isMerchantConfirmation(item))
}

function buildPublishableDetail(preview: any, copy?: any): string {
  const rawDetail = String(
    preview?.adapted_detail
    || preview?.detail
    || preview?.detail_copy
    || copy?.adapted_detail
    || copy?.detail_copy
    || '',
  )
  const sectionOverview = extractDetailSection(rawDetail, '商品概览')
  const overview = cleanPublishableBlock(
    sectionOverview || (!rawDetail.includes('【') ? rawDetail : ''),
  )
  const points = getPublishableSellingPoints(preview, copy)
  const audience = cleanPublishableBlock(String(copy?.target_audience || copy?.targetAudience || form.targetAudience || ''))
  const scenes = uniqueTextItems(copy?.usage_scenarios || copy?.usageScenarios || form.usageScenarios)
    .filter(item => !isMerchantConfirmation(item))
  const sections: string[] = []

  if (overview) sections.push(`【商品概览】\n${overview}`)
  if (points.length > 0) sections.push(`【核心亮点】\n${points.map(point => `• ${point}`).join('\n')}`)
  if (audience || scenes.length > 0) {
    const lines = [
      audience ? `适用人群：${audience}` : '',
      scenes.length > 0 ? `使用场景：${scenes.join('、')}` : '',
    ].filter(Boolean)
    sections.push(`【适用人群与场景】\n${lines.join('\n')}`)
  }

  if (sections.length > 0) return sections.join('\n\n')
  return cleanPublishableBlock(rawDetail)
}

function selectedPreviewFromResult(result: any, copy: any): any {
  const adaptation = result?.style_adaptation || {}
  const selectedStyle = adaptation.target_style || form.style
  return adaptation.previews?.[selectedStyle]
    || adaptation.platform_previews?.[selectedStyle]
    || adaptation
    || copy
}

function applyGeneratedDescription(preview: any, copy: any) {
  const detail = buildPublishableDetail(preview, copy)
  if (!detail) return
  form.description = detail
  aiFields.description = true
  aiFields.aiDetail = detail
}

function mergeConfirmationItemsIntoSpecifications(copy: any, detail = '') {
  const operationalItems = [
    ...toTextItems(copy?.specifications),
    ...toTextItems(copy?.pending_confirmations),
    ...toTextItems(extractDetailSection(detail, '规格参数')),
    ...toTextItems(extractDetailSection(detail, '购买前核对')),
  ]
  const merged = uniqueTextItems(form.specifications, operationalItems)
  if (merged.length > 0) form.specifications = merged.join('，')
}

function fillExtendedCopy(copy: any) {
  if (!copy) return
  form.subtitle = String(copy.subtitle || form.subtitle || '')
  mergeConfirmationItemsIntoSpecifications(copy, String(copy.adapted_detail || copy.detail_copy || ''))
  form.targetAudience = String(copy.target_audience || copy.targetAudience || form.targetAudience || '')
  form.usageScenarios = asTextList(copy.usage_scenarios || copy.usageScenarios) || form.usageScenarios
  form.seoKeywords = asTextList(copy.seo_keywords || copy.seoKeywords) || form.seoKeywords
  form.promotionCopy = String(copy.promotion_copy || copy.promotionCopy || form.promotionCopy || '')
  const suggested = Number(copy.price_suggestion ?? copy.priceSuggestion)
  aiPriceSuggestionYuan.value = Number.isFinite(suggested) && suggested > 0 ? suggested : null
}

function buildAiStylePayload() {
  let styleAdaptation: any = null
  if (aiFields.aiStylePreviews) {
    try { styleAdaptation = JSON.parse(aiFields.aiStylePreviews) } catch { styleAdaptation = null }
  }
  return {
    style_adaptation: styleAdaptation,
    extended_content: {
      subtitle: form.subtitle,
      price_suggestion: aiPriceSuggestionYuan.value,
      specifications: form.specifications.split(/[,，\n]/).map(v => v.trim()).filter(Boolean),
      target_audience: form.targetAudience,
      usage_scenarios: form.usageScenarios.split(/[,，\n]/).map(v => v.trim()).filter(Boolean),
      seo_keywords: form.seoKeywords.split(/[,，\n]/).map(v => v.trim()).filter(Boolean),
      promotion_copy: form.promotionCopy,
    },
  }
}

function applyStylePreview(style: string) {
  form.style = style as PlatformStyle
  const preview = stylePreviews.value[style]
  if (preview) {
    const copy = agentFullData.value?.copy || {}
    if (preview.adapted_title) {
      form.title = preview.adapted_title
      aiFields.title = true
    }
    fillExtendedCopy(copy)
    mergeConfirmationItemsIntoSpecifications(copy, String(preview.adapted_detail || preview.detail || ''))
    applyGeneratedDescription(preview, copy)
    const publishablePoints = getPublishableSellingPoints(preview, copy)
    if (publishablePoints.length > 0) {
      aiFields.sellingPoints = publishablePoints
      aiFields.aiSellingPoints = JSON.stringify(publishablePoints)
    }
    ElMessage.success(`已应用「${getStyleLabel(style)}」文案，待确认信息已归入规格参数`)
  } else {
    ElMessage.success(`已切换为「${getStyleLabel(style)}」风格`)
  }
}

// ===== Image Upload =====
function beforeImageUpload(file: File) {
  const isImage = file.type.startsWith('image/')
  const isLt5M = file.size / 1024 / 1024 < 5
  if (!isImage) { ElMessage.error('只能上传图片文件'); return false }
  if (!isLt5M) { ElMessage.error('图片大小不能超过 5MB'); return false }
  return true
}

function onImageSuccess(response: any) {
  if (response.code === 10000) {
    form.images.push(response.data as string)
    ElMessage.success('图片上传成功')
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

function onImageError() { ElMessage.error('图片上传失败，请检查网络') }
function removeImage(index: number) { form.images.splice(index, 1) }

// ===== Save =====
async function saveProduct() {
  if (!form.title.trim() || !form.category || !form.priceYuan || form.priceYuan <= 0) {
    ElMessage.warning('发布前请填写商品名称、品类和大于 0 的基础价格')
    return
  }
  saving.value = true
  try {
    const payload: any = {
      title: form.title,
      subtitle: form.subtitle,
      category: form.category || '其他',
      description: form.description,
      price: Math.round(form.priceYuan * 100),
      style: form.style,
      images: form.images.length > 0 ? JSON.stringify(form.images) : null,
    }
    if (aiFields.aiTitle) payload.aiTitle = aiFields.aiTitle
    if (aiFields.aiSellingPoints) payload.aiSellingPoints = aiFields.aiSellingPoints
    if (aiFields.aiDetail || aiFields.description) payload.aiDetail = aiFields.aiDetail || form.description
    payload.aiStylePreviews = JSON.stringify(buildAiStylePayload())
    if (aiFields.marketInsights) payload.marketInsights = aiFields.marketInsights
    if (aiFields.complianceResult) payload.complianceResult = aiFields.complianceResult

    let savedProduct: any
    if (isEdit.value) {
      savedProduct = await productApi.update(Number(route.params.id), payload)
    } else {
      savedProduct = await productApi.create(payload)
    }
    if (currentJobId.value) {
      await fetch(`/api/ai/jobs/${currentJobId.value}/consume`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('jmall-token')}` },
      }).catch(() => {})
      localStorage.setItem(JOB_CONSUMED_KEY, currentJobId.value)
      localStorage.removeItem(JOB_STORAGE_KEY)
      currentJobId.value = null
    }
    const notice = isEdit.value ? 'updated' : 'published'
    const savedId = savedProduct?.id || route.params.id || ''
    // This route is also the create page, so a same-route router.push would
    // leave the old form visible. A full navigation guarantees a clean editor.
    window.location.assign(`/merchant/products?notice=${notice}&id=${savedId}`)
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

// ===== Job Reconnection =====
async function findActiveJobId(excludedJobId?: string): Promise<string | null> {
  try {
    const activeResp = await fetch('/api/ai/jobs/active', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jmall-token')}` },
    })
    if (!activeResp.ok) return null
    const activeResult = await activeResp.json()
    const activeJob = activeResult?.data || activeResult
    const activeJobId = activeJob?.jobId || null
    const consumedJobId = localStorage.getItem(JOB_CONSUMED_KEY)
    return activeJobId && activeJobId !== excludedJobId && activeJobId !== consumedJobId
      ? activeJobId
      : null
  } catch {
    return null
  }
}

async function pollJobStatus(jobId: string) {
  try {
    const resp = await fetch(`/api/ai/jobs/${jobId}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('jmall-token')}` },
    })
    if (!resp.ok) {
      // A stale browser id must not hide a newer durable server-side job.
      localStorage.removeItem(JOB_STORAGE_KEY)
      currentJobId.value = null
      if (resp.status === 404) {
        const activeJobId = await findActiveJobId(jobId)
        if (activeJobId) {
          currentJobId.value = activeJobId
          localStorage.setItem(JOB_STORAGE_KEY, activeJobId)
          await pollJobStatus(activeJobId)
        }
      }
      return
    }
    const result = await resp.json()
    const job = result?.data || result

    if (!job || !job.status) return

    // Restore the merchant facts captured by the durable server-side job.
    // New products have no database draft before publication, so local form
    // state alone is insufficient after a browser refresh.
    const submitted = job.productInfo || job.product_info
    if (submitted) {
      if (!form.title) form.title = String(submitted.title || '')
      if (!form.category) form.category = String(submitted.category || '')
      if (!form.description) form.description = String(submitted.description || '')
      if ((!isEdit.value || !form.priceYuan || form.priceYuan <= 0) && Number(submitted.price) > 0) {
        form.priceYuan = Number(submitted.price)
      }
    }
    if (job.targetStyle || job.target_style) {
      form.style = (job.targetStyle || job.target_style) as PlatformStyle
    }

    // Restore progress
    if (job.progress) {
      for (const stage of stageList) {
        const stageStatus = String(job.progress[stage.key] || '').toUpperCase()
        if (stageStatus === 'COMPLETED') {
          agentStages.value[stage.key] = 'completed'
        } else if (stageStatus === 'ERROR' || stageStatus === 'FAILED') {
          agentStages.value[stage.key] = 'error'
        } else if (agentStages.value[stage.key] !== 'completed') {
          agentStages.value[stage.key] = 'pending'
        }
      }
      // The currentStep tells us which was the last one
      if (job.currentStep && agentStages.value[job.currentStep]) {
        // Find next uncompleted
        markNextRunning()
      }
    }

    // Restore partial results
    if (job.marketInsights) {
      const mi = job.marketInsights
      marketInsights.value = mapMarketInsights(mi)
      const kc = (mi.hot_keywords || mi.keywords || []).length
      const tc = (mi.trends || []).length
      marketResearchDetail.value = `${tc}条趋势, ${kc}个热搜词`
    }
    if (job.ragQuality) {
      ragQuality.value = job.ragQuality
      const rq = job.ragQuality
      ragDetail.value = `${rq.result_count ?? 0}条结果`
    }
    if (job.complianceResult) {
      // Handle nested structure: {compliance_result: {...}, elapsed_ms: ...}
      const cr = job.complianceResult.compliance_result || job.complianceResult
      complianceResult.value = {
        passed: cr.status === 'passed',
        warnings: cr.warnings || [],
        errors: cr.issues || [],
        summary: cr.summary || '',
        checklist: cr.checklist || {},
      }
    }
    // Restore style previews and copy drafts from persisted job
    if (job.stylePreviews || job.copyDrafts) {
      const sp = job.stylePreviews || job.copyDrafts
      mergeStylePreviews(sp)
      const ptCount = (sp.adapted_selling_points || sp.selling_points || []).length
      copyDetail.value = ptCount > 0 ? `${ptCount}个卖点` : ''
    }

    // If job is completed, restore full result
    const jobStatus = String(job.status).toUpperCase()
    if (jobStatus === 'COMPLETED' && job.result) {
      const fr = job.result
      applyCostStats(job.costStats || job.cost_stats)
      agentStatus.value = '✅ Agent 团队完成任务!'
      agentFullData.value = fr
      agentComplete.value = true
      agentLoading.value = false
      for (const stage of stageList) {
        if (agentStages.value[stage.key] !== 'error') {
          agentStages.value[stage.key] = 'completed'
        }
      }
      // Auto-fill form from result
      if (fr?.style_adaptation?.target_style) {
        form.style = fr.style_adaptation.target_style
      }
      if (fr?.copy) {
        const copy = fr.copy
        if (copy.adapted_title || (copy.titles?.[0])) {
          form.title = copy.adapted_title || copy.titles[0]
          aiFields.title = true
        }
        const points = copy.adapted_selling_points || copy.selling_points || []
        if (points.length > 0) {
          const publishablePoints = getPublishableSellingPoints(copy, copy)
          aiFields.sellingPoints = publishablePoints
          aiFields.aiSellingPoints = JSON.stringify(publishablePoints)
        }
        fillExtendedCopy(copy)
        const selectedPreview = selectedPreviewFromResult(fr, copy)
        mergeConfirmationItemsIntoSpecifications(copy, String(selectedPreview?.adapted_detail || selectedPreview?.detail || ''))
        applyGeneratedDescription(selectedPreview, copy)
      }
      if (fr?.style_adaptation?.target_style) {
        mergeStylePreviews(fr.style_adaptation)
        form.style = fr.style_adaptation.target_style
        aiFields.style = true
      }
      agentCompleteSummary.value = 'Agent 任务已完成，表单已自动填充'
      ElMessage.success('✅ Agent 任务已完成，表单已自动填充')
      return
    }

    // If still running, show progress
    if (jobStatus === 'RUNNING' || jobStatus === 'PENDING') {
      agentActive.value = true
      agentLoading.value = true
      agentStatus.value = '🤖 Agent 团队正在后台运行...'
      // Poll again in 2 seconds
      setTimeout(() => {
        if (currentJobId.value) pollJobStatus(currentJobId.value)
      }, 2000)
    }

    // If error
    if (jobStatus === 'FAILED' || jobStatus === 'ERROR') {
      agentStatus.value = '❌ Agent 任务失败'
      agentLoading.value = false
      localStorage.removeItem(JOB_STORAGE_KEY)
      currentJobId.value = null
      ElMessage.error(job.error || 'Agent 任务失败')
    }
  } catch {
    // Polling failed, try again in 3 seconds
    setTimeout(() => {
      if (currentJobId.value) pollJobStatus(currentJobId.value)
    }, 3000)
  }
}

onMounted(async () => {
  const notice = String(route.query.notice || '')
  if (notice === 'published' || notice === 'updated') {
    ElMessage.success(notice === 'published' ? '商品已发布，表单已刷新' : '商品已更新，表单已刷新')
    router.replace({ name: 'merchant-products' }).catch(() => {})
  }
  // Check for active job (reconnection after page navigation)
  let savedJobId = localStorage.getItem(JOB_STORAGE_KEY)
  // Always reconcile with the server. The local id can point to an expired
  // task after a container restart while Redis still has the current job.
  const activeJobId = await findActiveJobId()
  if (activeJobId) {
    savedJobId = activeJobId
    localStorage.setItem(JOB_STORAGE_KEY, activeJobId)
  }
  if (savedJobId) {
    currentJobId.value = savedJobId
    agentActive.value = true
    agentLoading.value = true
    agentStatus.value = '🔄 正在重连 Agent 任务...'
    for (const stage of stageList) {
      agentStages.value[stage.key] = 'pending'
    }
    pollJobStatus(savedJobId)
  }

  // Fetch knowledge base ID
  try {
    const kbResp = await fetch('/api/ai/knowledge-bases', {
      headers: { Authorization: `Bearer ${localStorage.getItem('jmall-token')}` },
    })
    if (kbResp.ok) {
      const kbData = await kbResp.json()
      const kbs = kbData?.data || kbData || []
      if (Array.isArray(kbs) && kbs.length > 0) {
        const professionalKb = kbs.find((kb: any) =>
          String(kb.label || kb.name || '').includes('专业经营') && Number(kb.documentCount || 0) > 0
        )
        const demoKb = kbs.find((kb: any) => kb.label?.toLowerCase().includes('demo'))
        knowledgeBaseId.value = professionalKb?.id || demoKb?.id || kbs[0]?.id || ''
      }
    }
  } catch { /* non-critical */ }

  if (isEdit.value) {
    productApi.get(Number(route.params.id), false).then(p => {
      form.title = p.title
      form.subtitle = p.subtitle || ''
      form.category = p.category
      form.description = p.description || ''
      form.priceYuan = p.price / 100
      form.style = p.style
      if (p.aiTitle) aiFields.aiTitle = p.aiTitle
      if (p.aiSellingPoints) {
        aiFields.aiSellingPoints = String(p.aiSellingPoints)
        try { aiFields.sellingPoints = JSON.parse(String(p.aiSellingPoints)) } catch { /* legacy value */ }
      }
      if (p.aiDetail) aiFields.aiDetail = p.aiDetail
      if (p.aiStylePreviews) {
        try {
          const stored = typeof p.aiStylePreviews === 'string' ? JSON.parse(p.aiStylePreviews) : p.aiStylePreviews
          const extended = stored?.extended_content || {}
          fillExtendedCopy(extended)
          const adaptation = stored?.style_adaptation || stored
          aiFields.aiStylePreviews = JSON.stringify(adaptation)
        } catch { /* legacy value */ }
      }
      if (p.images) {
        const storedImages = p.images
        try {
          form.images = Array.isArray(storedImages) ? storedImages : JSON.parse(storedImages)
        } catch {
          form.images = typeof storedImages === 'string' ? storedImages.split(',').filter(Boolean) : []
        }
      }
    }).catch(() => {})
  }
})
</script>

<style scoped>
.product-editor { padding: 24px; max-width: 1400px; }
.editor-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.editor-card { border-radius: 12px; }
.agent-panel { position: sticky; top: 80px; }
.agent-panel-header { display: flex; justify-content: space-between; align-items: center; }
.agent-loading { text-align: center; padding: 24px; }
.agent-status { font-size: 13px; color: #666; margin-top: 8px; }
.agent-section { margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #eee; }
.agent-section h4 { margin: 0 0 12px; font-size: 15px; }
.trend-tags, .hot-keywords { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 8px; }
.price-range { margin-top: 8px; font-size: 13px; color: #666; }
.market-suggestions { margin-top: 8px; }
.market-suggestions p { font-size: 13px; color: #666; margin: 2px 0; }
.market-provenance { display: flex; flex-direction: column; gap: 2px; margin-top: 10px; font-size: 12px; color: #606266; }
.market-sources { display: flex; flex-direction: column; gap: 5px; margin-top: 10px; font-size: 12px; }
.market-sources a { color: #409eff; text-decoration: none; line-height: 1.4; word-break: break-all; }
.market-sources a:hover { text-decoration: underline; }
.market-source-warning { margin-top: 10px; }
.price-suggestion { display: flex; align-items: center; gap: 12px; }
.price-suggestion strong { color: #e74c3c; font-size: 20px; }

/* Image area */
.image-area { width: 100%; }
.image-list { display: flex; flex-wrap: wrap; gap: 12px; }
.image-item { position: relative; width: 120px; height: 120px; border-radius: 8px; overflow: hidden; border: 1px solid #e4e7ed; }
.image-item.generated { border: 2px dashed #67c23a; }
.image-item.fallback { border: 2px dashed #c0c4cc; opacity: 0.8; }
.uploaded-image { width: 100%; height: 100%; object-fit: cover; }
.image-actions { position: absolute; top: 4px; right: 4px; opacity: 0; transition: opacity 0.2s; }
.image-item:hover .image-actions { opacity: 1; }
.generated-label { position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.6); color: #fff; font-size: 10px; text-align: center; padding: 2px 0; }
.image-upload-trigger { width: 120px; height: 120px; }
.upload-placeholder {
  width: 120px; height: 120px; border: 2px dashed #dcdfe6;
  border-radius: 8px; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 4px;
  color: #999; cursor: pointer; transition: all 0.2s;
}
.upload-placeholder:hover { border-color: #409eff; color: #409eff; }
.upload-hint { font-size: 12px; color: #999; margin: 8px 0 0; }

/* Style cards */
.style-cards { display: flex; flex-direction: column; gap: 10px; }
.style-card { border: 2px solid #eee; border-radius: 10px; overflow: hidden; cursor: pointer; transition: all 0.2s; }
.style-card:hover { border-color: #c0c4cc; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.style-card.active { border-color: #409eff; box-shadow: 0 0 0 2px rgba(64,158,255,0.2); }
.style-card-bar {
  padding: 6px 12px; color: #fff; font-size: 12px; font-weight: 500;
  display: flex; align-items: center; gap: 4px;
}
.style-card-body { padding: 10px 12px; }
.style-card-title { font-weight: bold; margin-bottom: 6px; color: #303133; font-size: 14px; }
.style-card-points { margin: 0; padding-left: 16px; font-size: 12px; color: #666; }
.style-card-points li { margin-bottom: 2px; }
.style-card-detail { font-size: 11px; color: #999; margin-top: 6px; line-height: 1.5; }
.style-card-footer { padding: 8px 12px; background: #fafafa; border-top: 1px solid #eee; display: flex; justify-content: flex-end; }

/* Agent full data */
.agent-full-data { font-size: 13px; }
.data-row { margin-bottom: 8px; line-height: 1.6; }
.data-label { font-weight: 600; color: #606266; }

.compliance-pass { border-left: 3px solid #67c23a; padding-left: 12px; }
.compliance-fail { border-left: 3px solid #f56c6c; padding-left: 12px; }
.agent-collapsed {
  text-align: center; padding: 24px; background: #f5f7fa;
  border-radius: 12px; cursor: pointer; transition: background 0.2s;
}
.agent-collapsed:hover { background: #e8ecf1; }
.ai-badge { margin-left: 8px; vertical-align: middle; }
.ai-selling-points { display: flex; flex-wrap: wrap; gap: 6px; }
.selling-point-tag { font-size: 13px; }

/* Agent Progress Checklist */
.agent-checklist { margin-bottom: 16px; }
.checklist-item {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 8px;
  font-size: 13px; transition: background 0.2s;
}
.checklist-item.completed { color: #67c23a; }
.checklist-item.running { color: #409eff; background: #ecf5ff; font-weight: 500; }
.checklist-item.error { color: #f56c6c; }
.checklist-item.pending { color: #c0c4cc; }
.check-icon { font-size: 16px; }
.check-icon.done { color: #67c23a; }
.check-icon.running { color: #409eff; }
.check-icon.error { color: #f56c6c; }
.check-icon.pending { color: #dcdfe6; }
.checklist-label { flex: 0 0 auto; }
.stage-detail { font-size: 11px; color: #909399; margin-left: auto; }

/* RAG Quality */
.rag-quality { padding: 12px; background: #f8f9fa; border-radius: 8px; }
.quality-bar { display: flex; flex-direction: column; gap: 6px; }
.quality-level {
  display: inline-block; padding: 2px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 600; align-self: flex-start;
}
.quality-level.excellent { background: #e8f5e9; color: #2e7d32; }
.quality-level.good { background: #e3f2fd; color: #1565c0; }
.quality-level.fair { background: #fff3e0; color: #e65100; }
.quality-level.poor { background: #fce4ec; color: #c62828; }
.quality-level.empty { background: #f5f5f5; color: #9e9e9e; }
.quality-metrics { display: flex; flex-wrap: wrap; gap: 12px; font-size: 12px; color: #606266; }

/* Agent Complete */
.agent-complete { background: #f0f9eb; padding: 12px; border-radius: 8px; }
.complete-summary { font-size: 13px; color: #67c23a; margin: 0 0 8px; }
.cost-stats { font-size: 12px; }
.cost-breakdown { margin-top: 8px; color: #606266; }
.cost-breakdown summary { cursor: pointer; color: #409eff; }
.cost-row { display: flex; justify-content: space-between; gap: 12px; padding: 4px 0; border-bottom: 1px dashed #dcdfe6; }
</style>
