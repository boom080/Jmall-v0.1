<template>
  <div class="product-editor">
    <div class="editor-header">
      <h2>{{ isEdit ? '编辑商品' : '上架新商品' }}</h2>
      <div class="editor-actions">
        <el-button size="large" :loading="assessmentLoading" :disabled="agentLoading || assessmentLoading" @click="checkInputOnly">免费检查信息</el-button>
        <el-button type="primary" size="large" :loading="agentLoading" :disabled="agentLoading || assessmentLoading" @click="triggerAgent">
          <el-icon><MagicStick /></el-icon> AI 检查并生成
        </el-button>
        <div class="image-search-action" :title="imageSearchDisabledReason">
          <el-button
            type="success"
            plain
            size="large"
            :loading="imageSearchLoading"
            :disabled="!canSearchImageCandidates"
            :aria-label="canSearchImageCandidates ? '根据完善内容找图' : imageSearchDisabledReason"
            @click="searchImageCandidates"
          >🔎 根据完善内容找图</el-button>
          <span v-if="!canSearchImageCandidates" class="image-search-action-hint">{{ imageSearchDisabledReason }}</span>
        </div>
      </div>
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
                  <!-- Category Fallback Image -->
                  <div v-if="form.images.length === 0" class="image-item fallback">
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
                <p class="upload-hint">支持 JPG/PNG/WebP，单张不超过 5MB，最多 6 张；也可以让 Image Scout 搜索相似图片。</p>

                <div v-if="form.images.length === 0" class="image-scout">
                  <div class="image-scout-header">
                    <div>
                      <strong>🔎 Image Scout</strong>
                      <p>根据已确认的商品事实搜索 Google 图片，最多展示 3 个带来源候选。</p>
                    </div>
                  </div>
                  <el-alert
                    title="Jmall 只负责搜索和展示，不保证图片使用权，也不会移除水印。请在使用前自行核对。"
                    type="warning"
                    :closable="false"
                    show-icon
                  />
                  <p v-if="imageSearchMessage" class="image-search-message">{{ imageSearchMessage }}</p>
                  <div v-if="imageCandidates.length" class="image-candidates">
                    <article v-for="candidate in imageCandidates" :key="candidate.candidate_id" class="image-candidate-card">
                      <img
                        :src="candidate.thumbnail_url"
                        :alt="candidate.title || form.title"
                        class="candidate-thumbnail"
                        referrerpolicy="no-referrer"
                      />
                      <div class="candidate-body">
                        <strong>{{ candidate.title || '相似商品图片' }}</strong>
                        <span v-if="candidate.width && candidate.height" class="candidate-size">
                          {{ candidate.width }} × {{ candidate.height }}
                        </span>
                        <a
                          :href="candidate.source_page_url"
                          target="_blank"
                          rel="noopener noreferrer"
                        >来源：{{ candidate.source_name || candidate.author }}</a>
                        <div class="candidate-risks">
                          <el-tag
                            v-for="risk in candidate.risk_flags"
                            :key="risk"
                            size="small"
                            type="warning"
                            effect="plain"
                          >{{ imageRiskLabel(risk) }}</el-tag>
                        </div>
                        <ul v-if="candidate.risk_reasons.length" class="candidate-risk-reasons">
                          <li v-for="reason in candidate.risk_reasons" :key="reason">{{ reason }}</li>
                        </ul>
                        <el-button size="small" type="primary" @click="useImageCandidate(candidate)">使用此图</el-button>
                      </div>
                    </article>
                  </div>
                </div>
              </div>
            </el-form-item>

            <el-form-item label="商品说明 / 一段话需求">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="10"
                placeholder="可以直接写一段完整的话，例如：我想卖一款可拆洗的记忆棉 U 型枕，主要给经常出差的上班族在飞机和高铁上使用，尺寸为 30×28cm，希望突出便携和颈部支撑。"
                maxlength="5000"
                show-word-limit
              />
              <p class="input-guidance">写清楚“卖什么、有哪些真实特点、卖给谁”，使用场景可以帮助 AI 理解得更准；也可以尽量填写下方规格、人群和场景。AI 会先检查信息，信息不足时不会启动完整 Agent。</p>
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
              <el-select v-model="form.style" @change="handlePlatformChange">
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
            <el-alert
              v-if="publishBlockers.length"
              title="还不能发布，请先处理以下问题"
              type="warning"
              :closable="false"
              show-icon
              class="publish-blockers"
            >
              <ul>
                <li v-for="blocker in publishBlockers" :key="`${blocker.code}-${blocker.field}`">
                  {{ blocker.message }}
                </li>
              </ul>
            </el-alert>
            <el-form-item class="publish-actions">
              <template v-if="productStatus === 'published'">
                <el-button type="success" size="large" @click="savePublishedChanges" :loading="saving">保存修改</el-button>
                <el-button size="large" @click="unpublishAndSave" :loading="saving">下架并保存草稿</el-button>
              </template>
              <template v-else>
                <el-button size="large" @click="saveDraft" :loading="saving">保存草稿</el-button>
                <el-button type="success" size="large" @click="checkAndPublish" :loading="saving">检查并发布</el-button>
              </template>
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
                <span>🤖 AI 上架助手</span>
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
            <p v-if="platformSkillDisplay" class="platform-skill-meta">本次生成：{{ platformSkillDisplay }}</p>
            <el-alert
              v-if="platformSwitchPending"
              :title="`已切换到${getStyleLabel(platformSwitchPending.to)}，当前仍保留${getStyleLabel(platformSwitchPending.from)}文案，请重新生成后再使用新平台内容。`"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 16px;"
            />

            <!-- Input completeness gate -->
            <div
              v-if="inputAssessment"
              class="agent-section input-assessment"
              :class="inputAssessment.ready ? 'assessment-ready' : 'assessment-needs-input'"
            >
              <div class="assessment-title">
                <h4>{{ inputAssessment.ready ? '✅ 商品信息可以开始生成' : '🧩 请先补全商品信息' }}</h4>
                <strong>{{ inputAssessment.score }}%</strong>
              </div>
              <el-progress
                :percentage="inputAssessment.score"
                :status="inputAssessment.ready ? 'success' : 'warning'"
                :stroke-width="8"
                :show-text="false"
              />
              <p v-if="inputAssessment.summary" class="assessment-summary">{{ inputAssessment.summary }}</p>
              <div v-if="inputAssessment.understood.length" class="assessment-group">
                <span class="assessment-label">AI 已理解</span>
                <el-tag v-for="item in inputAssessment.understood" :key="item" size="small" type="success" effect="plain">{{ item }}</el-tag>
              </div>
              <div v-if="inputAssessment.missing.length" class="assessment-group">
                <span class="assessment-label">仍然缺少</span>
                <el-tag v-for="item in inputAssessment.missing" :key="item" size="small" type="warning" effect="plain">{{ item }}</el-tag>
              </div>
              <div v-if="inputAssessment.questions.length" class="assessment-questions">
                <strong>请补充：</strong>
                <ol>
                  <li v-for="question in inputAssessment.questions" :key="question">{{ question }}</li>
                </ol>
                <p>直接补充左侧原表单后再次检查即可；不必把示例全部填满，信息不足时不会调用模型或扣费。</p>
              </div>
            </div>

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
              <h4>{{ inputAssessment && !inputAssessment.ready ? '🧩 等待补充商品信息' : (agentHadErrors ? '⚠️ Agent 降级完成' : '✅ Agent 任务完成') }}</h4>
              <p class="complete-summary" :class="{ 'needs-input': inputAssessment && !inputAssessment.ready }">{{ agentCompleteSummary }}</p>
              <div v-if="pendingConfirmations.length" class="pending-confirmations">
                <strong>待商家确认：</strong>
                <ul>
                  <li v-for="item in pendingConfirmations" :key="item">{{ item }}</li>
                </ul>
              </div>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { productApi } from '@/services/products'
import { createEditorFunnel } from '@/services/editorTelemetry'
import {
  aiImageApi,
  buildSelectedImageSource,
  imageSearchInputHint,
  imageRiskLabel,
  normalizeAiDraftMeta,
  type ImageCandidate,
} from '@/services/aiImages'
import { useAuthStore } from '@/stores/auth'
import {
  buildPlatformDraftPayload,
  extractPlatformSkillMetadata,
  filterSinglePlatformResult,
  isEditablePlatformContent,
  markEditablePlatformContent,
  mergePlatformDraftMeta,
  normalizePlatformDraft,
} from '@/utils/platformDraft'
import type { PlatformSkillMetadata, PlatformStyle, ProductStatus, PublishBlocker } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const editorFunnel = createEditorFunnel()

const isEdit = computed(() => !!route.params.id)
const saving = ref(false)
const savedDraftId = ref<number | null>(null)
const productStatus = ref<ProductStatus>('draft')
const publishBlockers = ref<PublishBlocker[]>([])
const agentActive = ref(true)
const agentLoading = ref(false)
const assessmentLoading = ref(false)
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

type InputAssessment = {
  status: string
  ready: boolean
  score: number
  understood: string[]
  missing: string[]
  questions: string[]
  summary: string
}

const inputAssessment = ref<InputAssessment | null>(null)

const stageList = [
  { key: 'input_assessment', label: '🧩 信息完整度检查' },
  { key: 'parse_intent', label: '🧠 解析意图' },
  { key: 'market_research', label: '🔍 市场调研' },
  { key: 'rag_retrieval', label: '📚 知识库检索' },
  { key: 'copy_generation', label: '✍️ 文案生成' },
  { key: 'style_adaptation', label: '🎨 风格适配' },
  { key: 'compliance_review', label: '⚖️ 合规审查' },
]

const agentHadErrors = computed(() => Object.values(agentStages.value).includes('error'))

function stageDetail(key: string): string {
  if (agentStages.value[key] === 'error') return agentErrors.value[key] || '该步骤已降级'
  if (agentStages.value[key] !== 'completed') return ''
  switch (key) {
    case 'input_assessment': return inputAssessment.value?.ready ? '信息已达到生成门槛' : '等待补充商品信息'
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

function mergeStylePreviews(sp: any, targetStyle?: string) {
  if (!sp) return
  const requestedStyle = targetStyle || sp.target_style || sp.targetStyle || sp.style || form.style
  const normalized = filterSinglePlatformResult(sp, requestedStyle)
  const styleKey = normalized.target_style
  if (!styleKey) return

  // The editor deliberately owns one current result. Legacy five-platform
  // payloads are filtered by filterSinglePlatformResult before display.
  stylePreviews.value = { [styleKey]: normalized.style_adaptation }
  generatedPlatformStyle.value = styleKey
  const previousMeta = platformSkillMeta.value
  const incomingMeta = normalized.generation_metadata
  const sameTarget = previousMeta?.target_style === incomingMeta.target_style
  platformSkillMeta.value = sameTarget
    && !incomingMeta.fallback
    && incomingMeta.platform_skill_id === null
    && incomingMeta.platform_skill_version === null
    ? previousMeta
    : incomingMeta
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
const imageCandidates = ref<ImageCandidate[]>([])
const imageSearchLoading = ref(false)
const imageSearchMessage = ref('')
const imageSearchProvider = ref('')
const aiDraftMeta = ref<Record<string, unknown>>({})
const imageSearchRequestId = ref(0)
const platformSkillMeta = ref<PlatformSkillMetadata | null>(null)
const generatedPlatformStyle = ref<string | null>(null)
const platformSwitchPending = ref<{ from: string; to: string } | null>(null)
// Image Scout is intentionally tied to the latest completed AI result. The
// snapshot is captured only after generated fields have been written back to
// the form, so any subsequent merchant edit automatically invalidates it.
const lastCompletedGenerationSnapshot = ref<string | null>(null)

const platformSkillDisplay = computed(() => {
  const meta = platformSkillMeta.value
  if (!meta?.target_style) return ''
  if (meta.fallback) return `${getStyleLabel(meta.target_style)} · 演示模板（无实际 Skill ID/版本）`
  if (meta.platform_skill_id && meta.platform_skill_version) {
    return `${getStyleLabel(meta.target_style)} · Skill ${meta.platform_skill_id} / ${meta.platform_skill_version}`
  }
  if (meta.platform_skill_id) return `${getStyleLabel(meta.target_style)} · Skill ${meta.platform_skill_id} / 版本未记录`
  return `${getStyleLabel(meta.target_style)} · Skill 版本未记录`
})
const pendingConfirmations = computed(() => toTextItems(
  Object.prototype.hasOwnProperty.call(agentFullData.value?.draft || {}, 'pending_confirmations')
    ? agentFullData.value.draft.pending_confirmations
    : Object.prototype.hasOwnProperty.call(agentFullData.value?.copy || {}, 'pending_confirmations')
      ? agentFullData.value.copy.pending_confirmations
      : aiDraftMeta.value.pending_confirmations,
))

// Image upload
const uploadUrl = '/api/upload/image'
const uploadHeaders = computed(() => {
  const h: Record<string, string> = {}
  if (authStore.token) h.Authorization = `Bearer ${authStore.token}`
  return h
})

// ===== Image Scout =====
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

async function searchImageCandidates() {
  // Keep the guard inside the handler as well as on the button. This covers
  // keyboard/programmatic clicks and prevents stale form data from reaching
  // the provider while a generation or edit is in flight.
  const disabledReason = imageSearchDisabledReason.value
  if (disabledReason) {
    imageSearchMessage.value = disabledReason
    ElMessage.warning(disabledReason)
    return
  }
  const requestId = ++imageSearchRequestId.value
  const productInfo = buildImageSearchProductInfo()
  const inputHint = imageSearchInputHint(productInfo)
  if (inputHint) {
    imageSearchMessage.value = inputHint
    ElMessage.warning(inputHint)
    return
  }
  const inputSnapshot = buildImageSearchSnapshot()
  imageSearchLoading.value = true
  imageSearchMessage.value = ''
  imageCandidates.value = []
  try {
    const result = await aiImageApi.candidates(productInfo)
    if (
      requestId !== imageSearchRequestId.value
      || form.images.length > 0
      || lastCompletedGenerationSnapshot.value !== inputSnapshot
      || buildImageSearchSnapshot() !== inputSnapshot
    ) {
      if (requestId === imageSearchRequestId.value && form.images.length === 0) {
        imageSearchMessage.value = '表单已修改，请重新执行 AI 检查并生成后再搜索图片'
      }
      return
    }
    imageSearchProvider.value = result.provider || ''
    const assessment = normalizeInputAssessment(result.input_assessment)
    if (assessment) inputAssessment.value = assessment
    if (result.status === 'needs_input') {
      imageSearchMessage.value = result.message || '请先补全商品信息，再搜索图片'
      ElMessage.warning(inputAssessment.value?.questions[0] || imageSearchMessage.value)
      return
    }
    imageCandidates.value = Array.isArray(result.candidates) ? result.candidates.slice(0, 3) : []
    imageSearchMessage.value = result.message || (
      imageCandidates.value.length
        ? `找到 ${imageCandidates.value.length} 个相关候选，请核对来源和风险后选择`
        : '没有找到来源完整的相关图片，请调整商品信息或上传自有图片'
    )
    if (!imageCandidates.value.length) {
      ElMessage.warning(imageSearchMessage.value)
    }
  } catch (error: any) {
    imageSearchMessage.value = error?.message || '图片检索失败，请稍后重试或上传自有图片'
    ElMessage.error(imageSearchMessage.value)
  } finally {
    if (requestId === imageSearchRequestId.value) imageSearchLoading.value = false
  }
}

async function useImageCandidate(candidate: ImageCandidate) {
  const riskSummary = candidate.risk_reasons.length
    ? `\n\n需要核对：${candidate.risk_reasons.join('；')}`
    : ''
  try {
    await ElMessageBox.confirm(
      `图片来自「${candidate.source_name || candidate.author}」。Jmall 仅提供检索和展示，不保证图片使用权。请确认你将自行核对并承担后续使用责任。${riskSummary}`,
      '使用搜索图片前确认',
      {
        type: 'warning',
        confirmButtonText: '我已了解，使用此图',
        cancelButtonText: '暂不使用',
      },
    )
  } catch {
    return
  }
  form.images = [candidate.original_url]
  aiDraftMeta.value.selected_image_source = buildSelectedImageSource(
    candidate,
    imageSearchProvider.value,
  )
  imageCandidates.value = []
  ElMessage.success('已选择搜索图片，来源与风险确认已记录')
  editorFunnel.imageResolved()
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

function toTextArray(value: unknown): string[] {
  if (Array.isArray(value)) return value.map(item => String(item).trim()).filter(Boolean)
  if (typeof value === 'string' && value.trim()) return [value.trim()]
  return []
}

function normalizeInputAssessment(payload: any): InputAssessment | null {
  const candidates = [
    payload?.data?.input_assessment,
    payload?.data?.inputAssessment,
    payload?.data?.assessment,
    payload?.data,
    payload?.input_assessment,
    payload?.inputAssessment,
    payload?.assessment,
    payload,
  ]
  const raw = candidates.find(candidate => candidate && typeof candidate === 'object'
    && (candidate.status !== undefined || candidate.ready !== undefined || candidate.questions !== undefined))
  if (!raw) return null

  const status = String(raw.status || (raw.ready ? 'ready' : 'needs_input'))
  const ready = typeof raw.ready === 'boolean'
    ? raw.ready
    : ['ready', 'complete', 'sufficient'].includes(status.toLowerCase())
  const rawScore = Number(raw.score ?? raw.completeness_score ?? (ready ? 100 : 0))

  return {
    status,
    ready,
    score: Math.max(0, Math.min(100, Number.isFinite(rawScore) ? Math.round(rawScore) : 0)),
    understood: toTextArray(raw.understood ?? raw.understood_items ?? raw.confirmed_facts ?? raw.confirmedFacts),
    missing: toTextArray(raw.missing ?? raw.missing_fields ?? raw.missing_critical_fields ?? raw.missingCriticalFields),
    questions: toTextArray(raw.questions).slice(0, 3),
    summary: String(raw.summary || raw.reason || ''),
  }
}

function buildAgentRequest() {
  return {
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
  }
}

function buildImageSearchProductInfo(): Record<string, unknown> {
  const { productInfo } = buildAgentRequest()
  return {
    ...productInfo,
    // These fields are generated/enriched by the selected platform Skill and
    // should be available to Image Scout when the backend accepts them.
    subtitle: form.subtitle,
    seo_keywords: form.seoKeywords
      .split(/[,，\n；;]+/)
      .map(item => item.trim())
      .filter(Boolean),
  }
}

function buildImageSearchSnapshot(): string {
  return JSON.stringify({
    productInfo: buildImageSearchProductInfo(),
    targetStyle: form.style,
    // A promotion edit is not sent to the image provider, but it is still a
    // form edit. Requiring a fresh generation keeps the button's state honest.
    promotionCopy: form.promotionCopy,
  })
}

const imageSearchDisabledReason = computed(() => {
  if (form.images.length > 0) return '已有商品图片；如需搜索候选，请先移除现有图片'
  if (imageSearchLoading.value) return '图片搜索进行中，请稍候'
  if (assessmentLoading.value || agentLoading.value) return 'AI 正在检查或完善商品信息，请等待完成'
  if (agentDemoMode.value) return '当前是安全降级模板，无法确认完善后的信息；请重试 AI 检查并生成'
  if (!agentComplete.value || !lastCompletedGenerationSnapshot.value || !generatedPlatformStyle.value) {
    return '请先完成 AI 检查并生成，AI 完善信息后才能搜索图片'
  }
  if (lastCompletedGenerationSnapshot.value !== buildImageSearchSnapshot()) {
    return '表单已修改，请重新执行 AI 检查并生成后再搜索图片'
  }
  return ''
})

const canSearchImageCandidates = computed(() => !imageSearchDisabledReason.value)

async function preflightInputAssessment(requestPayload: ReturnType<typeof buildAgentRequest>): Promise<InputAssessment> {
  const response = await fetch('/api/ai/input-assessment', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('jmall-token')}`,
    },
    body: JSON.stringify(requestPayload),
  })
  const body = await response.json().catch(() => null)
  if (!response.ok || (body?.code !== undefined && Number(body.code) !== 10000)) {
    throw new Error(body?.msg || body?.message || `HTTP ${response.status}`)
  }
  const assessment = normalizeInputAssessment(body)
  if (!assessment) throw new Error('输入检查服务没有返回有效结果')
  return assessment
}

async function releaseNeedsInputJob() {
  const jobId = currentJobId.value
  localStorage.removeItem(JOB_STORAGE_KEY)
  currentJobId.value = null
  if (!jobId) return
  localStorage.setItem(JOB_CONSUMED_KEY, jobId)
  await fetch(`/api/ai/jobs/${jobId}/consume`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${localStorage.getItem('jmall-token')}` },
  }).catch(() => {})
}

async function checkInputOnly() {
  if (assessmentLoading.value || agentLoading.value) return
  assessmentLoading.value = true
  agentActive.value = true
  const request = buildAgentRequest()
  const snapshot = JSON.stringify(request)
  try {
    const assessment = await preflightInputAssessment(request)
    if (JSON.stringify(buildAgentRequest()) !== snapshot) {
      ElMessage.info('表单已变化，请重新检查最新信息')
      return
    }
    inputAssessment.value = assessment
    if (assessment.ready) ElMessage.success('信息已达到生成门槛；本次仅检查，未启动模型或扣费')
  } catch (error: any) {
    ElMessage.error(error?.message || '信息检查失败，请稍后重试')
  } finally { assessmentLoading.value = false }
}

// ===== AI Agent Orchestration =====
async function triggerAgent() {
  if (agentLoading.value || assessmentLoading.value) return
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
  lastCompletedGenerationSnapshot.value = null
  agentCompleteSummary.value = ''
  agentCostStats.value = ''
  agentTokenBreakdown.value = []
  agentStatus.value = '🧩 正在检查商品信息是否完整...'
  inputAssessment.value = null

  // Reset
  marketInsights.value = null
  stylePreviews.value = {}
  generatedPlatformStyle.value = null
  platformSkillMeta.value = null
  platformSwitchPending.value = null
  delete aiDraftMeta.value.platform_switch_pending
  complianceResult.value = null
  agentFullData.value = null
  imageCandidates.value = []
  imageSearchMessage.value = ''
  ragQuality.value = null
  marketResearchDetail.value = ''
  ragDetail.value = ''
  copyDetail.value = ''
  agentErrors.value = {}

  // Initialize all stages as pending
  for (const stage of stageList) {
    agentStages.value[stage.key] = 'pending'
  }
  agentStages.value['input_assessment'] = 'running'

  const requestPayload = buildAgentRequest()
  try {
    inputAssessment.value = await preflightInputAssessment(requestPayload)
    agentStages.value['input_assessment'] = 'completed'
  } catch (e: any) {
    agentStages.value['input_assessment'] = 'error'
    agentErrors.value['input_assessment'] = e.message || '输入检查服务不可用'
    agentLoading.value = false
    agentComplete.value = true
    agentCompleteSummary.value = '无法确认商品信息是否完整，完整 Agent 未启动'
    agentStatus.value = '❌ 商品信息检查失败'
    ElMessage.error('商品信息检查失败，未启动 Agent，也不会扣除 Agent 使用金币')
    return
  }

  if (!inputAssessment.value.ready) {
    agentLoading.value = false
    agentComplete.value = true
    agentCompleteSummary.value = '商品信息尚未形成完整闭环，其他 Agent 未启动，也不会扣除 Agent 使用金币'
    agentStatus.value = '🧩 请根据右侧问题补充信息'
    ElMessage.warning(inputAssessment.value.questions[0] || '请先补充商品信息，再启动 Agent')
    return
  }

  agentStages.value['parse_intent'] = 'running'
  agentStatus.value = '🤖 信息检查通过，Agent 团队正在启动...'

  try {
    const response = await fetch('/api/ai/orchestrate/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('jmall-token')}`,
      },
      body: JSON.stringify(requestPayload),
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
              const agent = data.agent === 'input_validation' ? 'input_assessment' : data.agent

              const assessment = normalizeInputAssessment(data.input_assessment || data.inputAssessment)
              if (assessment) {
                inputAssessment.value = assessment
                agentStatus.value = assessment.ready
                  ? '🤖 信息检查通过，Agent 团队正在执行...'
                  : '🧩 商品信息不足，其他 Agent 已停止'
              }

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
              if (agent !== 'input_assessment') markNextRunning()

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
                const currentPreview = generatedPlatformStyle.value
                  ? stylePreviews.value[generatedPlatformStyle.value]
                  : sp
                const ptCount = (currentPreview?.adapted_selling_points || currentPreview?.selling_points || []).length
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
              const fr = data.final_result || data
              const status = fr?.overall_status || 'success'
              const finalAssessment = normalizeInputAssessment(fr?.input_assessment || data.input_assessment)
              if (finalAssessment) inputAssessment.value = finalAssessment
              agentFullData.value = fr

              if (status === 'needs_input' || status === 'insufficient_input') {
                agentStatus.value = '🧩 商品信息不足，完整 Agent 未启动'
                agentStages.value['input_assessment'] = 'completed'
                for (const stage of stageList) {
                  if (stage.key !== 'input_assessment') agentStages.value[stage.key] = 'pending'
                }
                agentCompleteSummary.value = '请补充右侧问题后重试；市场调研、RAG、文案、审核和风格 Agent 均未运行'
                agentComplete.value = true
                agentLoading.value = false
                await releaseNeedsInputJob()
                ElMessage.warning(inputAssessment.value?.questions[0] || '商品信息不足，请补充后重试')
                eventName = ''
                continue
              }

              agentStatus.value = '✅ Agent 团队完成任务!'

              // Mark all pending stages as completed
              for (const stage of stageList) {
                if (agentStages.value[stage.key] === 'pending' || agentStages.value[stage.key] === 'running') {
                  agentStages.value[stage.key] = 'completed'
                }
              }

              // Completion summary
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
              const normalizedFinal = applyPlatformResultMetadata(fr)
              const hasUnifiedFinalDraft = Boolean(fr?.style_adaptation?.draft || fr?.draft)
              const finalDraft = normalizedFinal?.draft || fr?.copy
              if (finalDraft) {
                const copy = finalDraft
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
                fillExtendedCopy(copy, hasUnifiedFinalDraft)
                const selectedPreview = selectedPreviewFromResult(fr, copy)
                mergeConfirmationItemsIntoSpecifications(
                  copy,
                  String(selectedPreview?.adapted_detail || selectedPreview?.detail || ''),
                  hasUnifiedFinalDraft,
                )
                applyGeneratedDescription(selectedPreview, copy)
              }
              if (normalizedFinal?.draft) {
                agentFullData.value = {
                  ...fr,
                  copy: normalizedFinal.draft,
                  draft: normalizedFinal.draft,
                  style_adaptation: normalizedFinal.style_adaptation,
                  generation_metadata: {
                    ...(fr?.generation_metadata || {}),
                    ...normalizedFinal.generation_metadata,
                  },
                }
              }
              if (fr?.market_insights) {
                marketInsights.value = mapMarketInsights(fr.market_insights)
                aiFields.marketInsights = JSON.stringify(fr.market_insights)
              }
              if (fr?.compliance) {
                aiFields.complianceResult = JSON.stringify(fr.compliance)
              }
              // applyPlatformResultMetadata has already filtered legacy
              // previews to the selected target and persisted Skill metadata.
              if (!normalizedFinal?.target_style && fr?.style_adaptation) {
                mergeStylePreviews(fr.style_adaptation)
              }

              // All generated fields have now been applied. Capture the
              // post-generation form state for Image Scout's stale-data gate.
              lastCompletedGenerationSnapshot.value = buildImageSearchSnapshot()

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

  // Only expose the requested platform. The fallback is a local demo
  // template, so it intentionally carries no Skill id or version.
  const selectedStyle = form.style
  const pd = getPlatformDemoData(selectedStyle)
  const merchantHighlights = form.description
    .split(/[\n。；;]+/)
    .map(item => item.trim())
    .filter(item => item && !isMerchantConfirmation(item))
    .slice(0, 5)
  const title = `${pd.titlePrefix}${form.title || '商品'}`
  const points = merchantHighlights.length > 0 ? merchantHighlights : pd.selling_points
  const detail = form.description || `请补充「${form.title || '商品'}」的真实规格、特点、使用场景与售后信息。`
  const demoDraft = {
    titles: [title],
    selling_points: points,
    detail_copy: detail,
    subtitle: `${category}商品信息待完善`,
    price_suggestion: null,
    specifications: ['请补充可核验规格'],
    target_audience: '请根据真实适用范围补充',
    usage_scenarios: ['请根据真实用途补充'],
    seo_keywords: [form.title, category].filter(Boolean),
    promotion_copy: `${title}，价格与优惠以商家实际设置为准。`,
    short_video_script: '',
    pending_confirmations: ['这是安全降级演示模板，不代表实际平台 Skill 生成结果'],
  }
  const demoAdaptation = {
    target_style: selectedStyle,
    adapted_title: title,
    adapted_selling_points: points,
    adapted_detail: detail,
    draft: demoDraft,
    style_notes: `${pd.styleNote} 当前为演示降级模板，无实际平台 Skill ID/版本。`,
    platform_skill_id: null,
    platform_skill_version: null,
    pending_confirmations: demoDraft.pending_confirmations,
    fallback: true,
  }
  const demoResult = filterSinglePlatformResult({
    style_adaptation: demoAdaptation,
    generation_metadata: {
      target_style: selectedStyle,
      platform_skill_id: null,
      platform_skill_version: null,
      fallback: true,
    },
  }, selectedStyle)
  stylePreviews.value = { [selectedStyle]: demoResult.style_adaptation }
  generatedPlatformStyle.value = selectedStyle
  platformSkillMeta.value = demoResult.generation_metadata
  platformSwitchPending.value = null

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
    copy: demoResult.draft,
    draft: demoResult.draft,
    style_adaptation: demoResult.style_adaptation,
    generation_metadata: demoResult.generation_metadata,
    overall_status: 'needs_revision',
  }
  fillExtendedCopy(demoResult.draft, true)
  aiFields.aiStylePreviews = JSON.stringify(buildPlatformDraftPayload(
    demoResult,
    demoResult.generation_metadata,
    demoResult.draft,
    selectedStyle,
  ))
  aiDraftMeta.value = mergePlatformDraftMeta(aiDraftMeta.value, demoResult, selectedStyle)
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

function cleanUnifiedDraftDetail(value: string): string {
  return value
    .split(/\n+/)
    .map(line => line.trim())
    .filter(line => line && (/^【[^】]+】$/.test(line) || !isMerchantConfirmation(line)))
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
  const unifiedDraft = preview?.draft || copy?.draft
  if (unifiedDraft && Object.prototype.hasOwnProperty.call(unifiedDraft, 'detail_copy')) {
    // M4 platform Skills own the complete document structure. Keep headings
    // such as 商品信息/规格参数 intact; only drop explicit confirmation lines.
    return cleanUnifiedDraftDetail(String(unifiedDraft.detail_copy || ''))
  }
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
  const adaptation = result?.style_adaptation || result || {}
  const selectedStyle = adaptation.target_style || result?.generation_metadata?.target_style || form.style
  if (!result?.style_adaptation?.draft && !result?.draft) {
    return adaptation.previews?.[selectedStyle]
      || adaptation.platform_previews?.[selectedStyle]
      || adaptation
      || copy
  }
  const normalized = filterSinglePlatformResult(result, selectedStyle)
  return normalized.style_adaptation || normalized.draft || copy
}

function applyPlatformResultMetadata(result: any) {
  if (!result) return null
  const requestedStyle = result?.style_adaptation?.target_style
    || result?.generation_metadata?.target_style
    || result?.target_style
    || form.style
  const normalized = filterSinglePlatformResult(result, requestedStyle)
  if (!normalized.target_style) return normalized

  mergeStylePreviews(result, normalized.target_style)
  form.style = normalized.target_style as PlatformStyle
  aiFields.style = true
  generatedPlatformStyle.value = normalized.target_style
  platformSkillMeta.value = normalized.generation_metadata
  platformSwitchPending.value = null
  delete aiDraftMeta.value.platform_switch_pending

  const persisted = buildPlatformDraftPayload(
    result,
    result?.generation_metadata,
    result?.draft || result?.copy || normalized.draft,
    normalized.target_style,
  )
  aiFields.aiStylePreviews = JSON.stringify(persisted)
  aiDraftMeta.value = mergePlatformDraftMeta(
    aiDraftMeta.value,
    persisted,
    normalized.target_style,
  )
  return normalized
}

function applyGeneratedDescription(preview: any, copy: any) {
  const detail = buildPublishableDetail(preview, copy)
  if (!detail) return
  form.description = detail
  aiFields.description = true
  aiFields.aiDetail = detail
}

function mergeConfirmationItemsIntoSpecifications(copy: any, detail = '', authoritativeDraft = false) {
  // Pending confirmations are evidence gaps, not product facts. They remain
  // in aiDraftMeta/confirmation panel and never become publishable specs for
  // the unified platform draft. Keep the old extraction only for legacy data.
  // fillExtendedCopy already replaced specifications from the unified draft.
  // Re-merging its array with the rendered comma-joined text duplicates it
  // on both stream completion and recovery. Only legacy data needs merging.
  if (authoritativeDraft) return
  const operationalItems = [
      ...toTextItems(copy?.specifications),
      ...toTextItems(copy?.pending_confirmations),
      ...toTextItems(extractDetailSection(detail, '规格参数')),
      ...toTextItems(extractDetailSection(detail, '购买前核对')),
    ]
  const merged = uniqueTextItems(form.specifications, operationalItems)
  if (merged.length > 0) form.specifications = merged.join('，')
}

function fillExtendedCopy(copy: any, authoritativeDraft = false) {
  if (!copy) return
  const has = (...keys: string[]) => keys.some(key => Object.prototype.hasOwnProperty.call(copy, key))
  const value = (...keys: string[]) => keys.find(key => copy[key] !== undefined)
  const canApply = (raw: unknown) => authoritativeDraft || (raw !== undefined && raw !== null && String(raw).trim() !== '')
  if (has('subtitle') && canApply(copy.subtitle)) form.subtitle = String(copy.subtitle ?? '')
  if (has('specifications') && canApply(copy.specifications)) form.specifications = asTextList(copy.specifications)
  mergeConfirmationItemsIntoSpecifications(
    copy,
    String(copy.adapted_detail || copy.detail_copy || ''),
    authoritativeDraft,
  )
  if (has('target_audience', 'targetAudience')) {
    const key = value('target_audience', 'targetAudience')
    if (canApply(key ? copy[key] : undefined)) form.targetAudience = String(key ? copy[key] ?? '' : '')
  }
  if (has('usage_scenarios', 'usageScenarios')) {
    const key = value('usage_scenarios', 'usageScenarios')
    if (canApply(key ? copy[key] : undefined)) form.usageScenarios = asTextList(key ? copy[key] : [])
  }
  if (has('seo_keywords', 'seoKeywords')) {
    const key = value('seo_keywords', 'seoKeywords')
    if (canApply(key ? copy[key] : undefined)) form.seoKeywords = asTextList(key ? copy[key] : [])
  }
  if (has('promotion_copy', 'promotionCopy')) {
    const key = value('promotion_copy', 'promotionCopy')
    if (canApply(key ? copy[key] : undefined)) form.promotionCopy = String(key ? copy[key] ?? '' : '')
  }
  if (has('price_suggestion', 'priceSuggestion')) {
    const key = value('price_suggestion', 'priceSuggestion')
    if (canApply(key ? copy[key] : undefined)) {
      const suggested = Number(key ? copy[key] : null)
      aiPriceSuggestionYuan.value = Number.isFinite(suggested) && suggested > 0 ? suggested : null
    }
  }
}

function buildAiStylePayload() {
  let storedPayload: any = null
  if (aiFields.aiStylePreviews) {
    try { storedPayload = JSON.parse(aiFields.aiStylePreviews) } catch { storedPayload = null }
  }
  const extendedContent = markEditablePlatformContent({
    // This snapshot reflects the editable form at save time. It lets a
    // reload restore merchant edits while the Skill draft remains the
    // immutable/generated preview source.
    subtitle: form.subtitle,
    price_suggestion: aiPriceSuggestionYuan.value,
    specifications: form.specifications.split(/[,，\n]/).map(v => v.trim()).filter(Boolean),
    target_audience: form.targetAudience,
    usage_scenarios: form.usageScenarios.split(/[,，\n]/).map(v => v.trim()).filter(Boolean),
    seo_keywords: form.seoKeywords.split(/[,，\n]/).map(v => v.trim()).filter(Boolean),
    promotion_copy: form.promotionCopy,
  })
  const source = storedPayload || (
    generatedPlatformStyle.value && stylePreviews.value[generatedPlatformStyle.value]
      ? { style_adaptation: stylePreviews.value[generatedPlatformStyle.value] }
      : null
  )
  if (!source) {
    return {
      style_adaptation: null,
      draft: normalizePlatformDraft(extendedContent),
      extended_content: extendedContent,
    }
  }
  return buildPlatformDraftPayload(
    source,
    storedPayload?.generation_metadata || platformSkillMeta.value,
    extendedContent,
    generatedPlatformStyle.value || storedPayload?.style_adaptation?.target_style || form.style,
  )
}

function handlePlatformChange(style: string) {
  const generatedStyle = generatedPlatformStyle.value
  if (!generatedStyle || style === generatedStyle) {
    if (style === generatedStyle) {
      platformSwitchPending.value = null
      delete aiDraftMeta.value.platform_switch_pending
    }
    return
  }
  platformSwitchPending.value = { from: generatedStyle, to: style }
  aiDraftMeta.value.platform_switch_pending = {
    from: generatedStyle,
    to: style,
    message: '切换平台后需要重新生成，当前表单仍保留原平台文案',
  }
  ElMessage.warning(`已切换到「${getStyleLabel(style)}」，当前仍保留「${getStyleLabel(generatedStyle)}」文案，请重新生成`)
}

function applyStylePreview(style: string) {
  form.style = style as PlatformStyle
  const preview = stylePreviews.value[style]
  if (preview && (!generatedPlatformStyle.value || generatedPlatformStyle.value === style)) {
    generatedPlatformStyle.value = style
    platformSkillMeta.value = extractPlatformSkillMetadata(preview, style)
    platformSwitchPending.value = null
    delete aiDraftMeta.value.platform_switch_pending
    const copy = preview.draft || agentFullData.value?.draft || agentFullData.value?.copy || {}
    if (preview.adapted_title) {
      form.title = preview.adapted_title
      aiFields.title = true
    }
    fillExtendedCopy(copy, true)
    mergeConfirmationItemsIntoSpecifications(copy, String(preview.adapted_detail || preview.detail || ''), true)
    applyGeneratedDescription(preview, copy)
    const publishablePoints = getPublishableSellingPoints(preview, copy)
    if (publishablePoints.length > 0) {
      aiFields.sellingPoints = publishablePoints
      aiFields.aiSellingPoints = JSON.stringify(publishablePoints)
    }
    aiFields.aiStylePreviews = JSON.stringify(buildPlatformDraftPayload(
      { style_adaptation: preview, draft: copy },
      platformSkillMeta.value,
      copy,
      style,
    ))
    aiDraftMeta.value = mergePlatformDraftMeta(aiDraftMeta.value, preview, style)
    agentFullData.value = {
      ...(agentFullData.value || {}),
      copy,
      draft: copy,
      style_adaptation: preview,
      generation_metadata: extractPlatformSkillMetadata(preview, style),
    }
    // Applying an already generated preview writes AI content into the form;
    // refresh the search snapshot only after those writes are complete.
    lastCompletedGenerationSnapshot.value = buildImageSearchSnapshot()
    ElMessage.success(`已应用「${getStyleLabel(style)}」文案，待确认信息已记录在待确认区域`)
  } else {
    handlePlatformChange(style)
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
    imageSearchRequestId.value += 1
    imageSearchLoading.value = false
    form.images.push(response.data as string)
    imageCandidates.value = []
    ElMessage.success('图片上传成功')
    editorFunnel.imageResolved()
  } else {
    ElMessage.error(response.msg || '上传失败')
  }
}

function onImageError() { ElMessage.error('图片上传失败，请检查网络') }
function removeImage(index: number) {
  const removed = form.images[index]
  form.images.splice(index, 1)
  if (!form.images.length) editorFunnel.noImage()
  const selected = aiDraftMeta.value.selected_image_source as Record<string, unknown> | undefined
  if (selected?.original_url === removed) delete aiDraftMeta.value.selected_image_source
}

// ===== Draft and publish =====
function buildProductPayload() {
  aiDraftMeta.value.input_snapshot = buildAgentRequest().productInfo
  if (inputAssessment.value) aiDraftMeta.value.input_assessment = inputAssessment.value
  const pending = toTextItems(agentFullData.value?.copy?.pending_confirmations)
  if (agentFullData.value?.copy && pending.length) aiDraftMeta.value.pending_confirmations = pending
  else if (agentFullData.value?.copy) delete aiDraftMeta.value.pending_confirmations

  const stylePayload = buildAiStylePayload()
  if (generatedPlatformStyle.value && stylePayload.style_adaptation) {
    aiDraftMeta.value = mergePlatformDraftMeta(
      aiDraftMeta.value,
      stylePayload,
      generatedPlatformStyle.value,
    )
  }

  const payload: any = {
    title: form.title.trim(),
    subtitle: form.subtitle,
    category: form.category,
    description: form.description,
    price: Math.max(0, Math.round((Number(form.priceYuan) || 0) * 100)),
    style: form.style,
    images: form.images.length > 0 ? JSON.stringify(form.images) : null,
    aiDraftMeta: JSON.stringify(aiDraftMeta.value),
  }
  if (aiFields.aiTitle) payload.aiTitle = aiFields.aiTitle
  if (aiFields.aiSellingPoints) payload.aiSellingPoints = aiFields.aiSellingPoints
  if (aiFields.aiDetail || aiFields.description) payload.aiDetail = aiFields.aiDetail || form.description
  payload.aiStylePreviews = JSON.stringify(stylePayload)
  if (aiFields.marketInsights) payload.marketInsights = aiFields.marketInsights
  if (aiFields.complianceResult) payload.complianceResult = aiFields.complianceResult
  return payload
}

function currentProductId(): number | null {
  const routeId = Number(route.params.id)
  return Number.isFinite(routeId) && routeId > 0 ? routeId : savedDraftId.value
}

async function persistCurrentProduct() {
  const id = currentProductId()
  const saved = id
    ? await productApi.update(id, buildProductPayload())
    : await productApi.create(buildProductPayload())
  savedDraftId.value = saved.id
  productStatus.value = saved.status
  if (saved.status === 'draft') editorFunnel.saved()
  return saved
}

function blockersFromError(error: any): PublishBlocker[] {
  const data = error?.data
  return Array.isArray(data?.publish_blockers) ? data.publish_blockers : []
}

async function consumeCurrentJob() {
  if (!currentJobId.value) return
  await fetch(`/api/ai/jobs/${currentJobId.value}/consume`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${localStorage.getItem('jmall-token')}` },
  }).catch(() => {})
  localStorage.setItem(JOB_CONSUMED_KEY, currentJobId.value)
  localStorage.removeItem(JOB_STORAGE_KEY)
  currentJobId.value = null
}

async function saveDraft() {
  saving.value = true
  publishBlockers.value = []
  try {
    const saved = await persistCurrentProduct()
    await consumeCurrentJob()
    window.location.assign(`/merchant/products?notice=drafted&id=${saved.id}`)
  } catch (error: any) {
    ElMessage.error(error?.message || '草稿保存失败')
  } finally { saving.value = false }
}

async function savePublishedChanges() {
  saving.value = true
  publishBlockers.value = []
  try {
    const saved = await persistCurrentProduct()
    await consumeCurrentJob()
    window.location.assign(`/merchant/products?notice=updated&id=${saved.id}`)
  } catch (error: any) {
    publishBlockers.value = blockersFromError(error)
    ElMessage.error(publishBlockers.value[0]?.message || error?.message || '修改保存失败')
  } finally { saving.value = false }
}

async function checkAndPublish() {
  saving.value = true
  publishBlockers.value = []
  try {
    const saved = await persistCurrentProduct()
    if (!route.params.id) await router.replace(`/merchant/products/${saved.id}`)
    const check = await productApi.publishCheck(saved.id)
    publishBlockers.value = check.publish_blockers || []
    if (!check.publishable) {
      ElMessage.warning(publishBlockers.value[0]?.message || '商品尚未通过发布检查')
      return
    }
    await ElMessageBox.confirm(
      '发布后商品将对买家可见并可购买。确认现在发布？',
      '确认发布',
      { type: 'warning', confirmButtonText: '确认发布', cancelButtonText: '继续编辑' },
    )
    await productApi.publish(saved.id)
    editorFunnel.published()
    await consumeCurrentJob()
    await router.push(`/merchant/products/${saved.id}/published`)
  } catch (error: any) {
    if (error === 'cancel' || error === 'close') return
    publishBlockers.value = blockersFromError(error)
    ElMessage.error(publishBlockers.value[0]?.message || error?.message || '发布失败')
  } finally { saving.value = false }
}

async function unpublishAndSave() {
  const id = currentProductId()
  if (!id) return
  saving.value = true
  try {
    await productApi.unpublish(id)
    productStatus.value = 'draft'
    await persistCurrentProduct()
    window.location.assign(`/merchant/products?notice=unpublished&id=${id}`)
  } catch (error: any) {
    ElMessage.error(error?.message || '下架失败')
  } finally { saving.value = false }
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
      if (!form.specifications) form.specifications = String(submitted.specifications || '')
      if (!form.targetAudience) form.targetAudience = String(submitted.target_audience || submitted.targetAudience || '')
      if (!form.usageScenarios) form.usageScenarios = String(submitted.usage_scenarios || submitted.usageScenarios || '')
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
    const restoredAssessment = normalizeInputAssessment(
      job.inputAssessment || job.input_assessment || job.result?.input_assessment
    )
    if (restoredAssessment) inputAssessment.value = restoredAssessment
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
    if (job.style_adaptation || job.styleAdaptation || job.stylePreviews || job.copyDrafts) {
      const sp = job.stylePreviews || job.copyDrafts
      const partialStyleResult = {
        ...(job.style_adaptation || job.styleAdaptation
          ? { style_adaptation: job.style_adaptation || job.styleAdaptation }
          : sp || {}),
        ...(job.generation_metadata || job.generationMetadata
          ? { generation_metadata: job.generation_metadata || job.generationMetadata }
          : {}),
      }
      mergeStylePreviews(
        partialStyleResult,
        job.targetStyle || job.target_style || form.style,
      )
      const restoredStyle = generatedPlatformStyle.value
      const restoredPreview = restoredStyle ? stylePreviews.value[restoredStyle] : null
      const ptCount = (restoredPreview?.adapted_selling_points || restoredPreview?.selling_points || []).length
      copyDetail.value = ptCount > 0 ? `${ptCount}个卖点` : ''
      if (restoredStyle) {
        aiDraftMeta.value = mergePlatformDraftMeta(
          aiDraftMeta.value,
          partialStyleResult,
          restoredStyle,
        )
      }
    }

    // If job is completed, restore full result
    const jobStatus = String(job.status).toUpperCase()
    if (jobStatus === 'COMPLETED' && job.result) {
      const fr = {
        ...job.result,
        ...(!job.result.generation_metadata && (job.generation_metadata || job.generationMetadata)
          ? { generation_metadata: job.generation_metadata || job.generationMetadata }
          : {}),
      }
      const finalStatus = String(fr?.overall_status || '')
      const finalAssessment = normalizeInputAssessment(fr?.input_assessment)
      if (finalAssessment) inputAssessment.value = finalAssessment

      if (finalStatus === 'needs_input' || finalStatus === 'insufficient_input') {
        agentStatus.value = '🧩 商品信息不足，完整 Agent 未启动'
        agentComplete.value = true
        agentLoading.value = false
        agentStages.value['input_assessment'] = 'completed'
        for (const stage of stageList) {
          if (stage.key !== 'input_assessment') agentStages.value[stage.key] = 'pending'
        }
        agentCompleteSummary.value = '请补充右侧问题后重试；其他 Agent 均未运行'
        await releaseNeedsInputJob()
        return
      }

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
      const normalizedFinal = applyPlatformResultMetadata(fr)
      const hasUnifiedFinalDraft = Boolean(fr?.style_adaptation?.draft || fr?.draft)
      const finalDraft = normalizedFinal?.draft || fr?.copy
      if (finalDraft) {
        const copy = finalDraft
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
        fillExtendedCopy(copy, hasUnifiedFinalDraft)
        const selectedPreview = selectedPreviewFromResult(fr, copy)
        mergeConfirmationItemsIntoSpecifications(
          copy,
          String(selectedPreview?.adapted_detail || selectedPreview?.detail || ''),
          hasUnifiedFinalDraft,
        )
        applyGeneratedDescription(selectedPreview, copy)
      }
      if (normalizedFinal?.draft) {
        agentFullData.value = {
          ...fr,
          copy: normalizedFinal.draft,
          draft: normalizedFinal.draft,
          style_adaptation: normalizedFinal.style_adaptation,
          generation_metadata: {
            ...(fr?.generation_metadata || {}),
            ...normalizedFinal.generation_metadata,
          },
        }
      }
      // Recovery follows the same contract as the live SSE path: only record
      // the snapshot after the completed result has populated the form.
      lastCompletedGenerationSnapshot.value = buildImageSearchSnapshot()
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
  editorFunnel.open(isEdit.value ? undefined : form.images.length > 0)
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
      productStatus.value = p.status
      savedDraftId.value = p.id
      if (p.aiTitle) aiFields.aiTitle = p.aiTitle
      if (p.aiSellingPoints) {
        aiFields.aiSellingPoints = String(p.aiSellingPoints)
        try { aiFields.sellingPoints = JSON.parse(String(p.aiSellingPoints)) } catch { /* legacy value */ }
      }
      if (p.aiDetail) aiFields.aiDetail = p.aiDetail
      if (p.complianceResult) {
        aiFields.complianceResult = typeof p.complianceResult === 'string'
          ? p.complianceResult
          : JSON.stringify(p.complianceResult)
      }
      if (p.aiDraftMeta) {
        aiDraftMeta.value = normalizeAiDraftMeta(p.aiDraftMeta)
      }
      if (p.aiStylePreviews) {
        try {
          const stored = typeof p.aiStylePreviews === 'string' ? JSON.parse(p.aiStylePreviews) : p.aiStylePreviews
          const storedMeta = extractPlatformSkillMetadata(stored, p.style)
          const pendingSwitch = aiDraftMeta.value.platform_switch_pending as Record<string, unknown> | undefined
          const restoredTarget = storedMeta.target_style || p.style
          const normalized = filterSinglePlatformResult(stored, restoredTarget)
          const hasStoredUnifiedDraft = Boolean(stored?.style_adaptation?.draft || stored?.draft)
          // Unified draft wins over the legacy extended_content envelope.
          const editableContent = isEditablePlatformContent(stored?.extended_content)
            ? stored.extended_content
            : normalized.draft || stored?.draft || stored?.extended_content || {}
          fillExtendedCopy(editableContent, hasStoredUnifiedDraft || isEditablePlatformContent(stored?.extended_content))
          mergeStylePreviews(stored, restoredTarget)
          generatedPlatformStyle.value = normalized.target_style || restoredTarget
          platformSkillMeta.value = extractPlatformSkillMetadata(
            stored,
            generatedPlatformStyle.value || p.style,
          )
          aiDraftMeta.value = mergePlatformDraftMeta(
            aiDraftMeta.value,
            stored,
            generatedPlatformStyle.value || p.style,
          )
          if (normalized.target_style && !pendingSwitch) {
            form.style = normalized.target_style as PlatformStyle
          }
          if (pendingSwitch?.from && pendingSwitch?.to) {
            platformSwitchPending.value = {
              from: String(pendingSwitch.from),
              to: String(pendingSwitch.to),
            }
          }
          agentFullData.value = {
            ...(agentFullData.value || {}),
            copy: normalized.draft,
            draft: normalized.draft,
            style_adaptation: normalized.style_adaptation,
            generation_metadata: normalized.generation_metadata,
          }
          aiFields.aiStylePreviews = JSON.stringify(buildPlatformDraftPayload(
            stored,
            stored?.generation_metadata || platformSkillMeta.value,
            stored?.extended_content || normalized.draft,
            generatedPlatformStyle.value || restoredTarget,
          ))
        } catch { /* legacy value */ }
      }
      if (!platformSkillMeta.value && p.aiDraftMeta) {
        const restoredMeta = extractPlatformSkillMetadata(aiDraftMeta.value, p.style)
        if (restoredMeta.target_style || restoredMeta.platform_skill_id || restoredMeta.platform_skill_version) {
          platformSkillMeta.value = restoredMeta
          generatedPlatformStyle.value = restoredMeta.target_style || p.style
        }
      }
      if (p.images) {
        const storedImages = p.images
        try {
          form.images = Array.isArray(storedImages) ? storedImages : JSON.parse(storedImages)
        } catch {
          form.images = typeof storedImages === 'string' ? storedImages.split(',').filter(Boolean) : []
        }
      }
      if (!form.images.length) editorFunnel.noImage()
    }).catch(() => {})
  }
})
</script>

<style scoped>
.product-editor { padding: 24px; max-width: 1400px; }
.editor-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.editor-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-start; }
.image-search-action { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; max-width: 280px; }
.image-search-action-hint { color: #909399; font-size: 12px; line-height: 1.4; }
.editor-card { border-radius: 12px; }
.input-guidance { margin: 8px 0 0; color: #606266; font-size: 12px; line-height: 1.6; }
.agent-panel { position: sticky; top: 80px; }
.agent-panel-header { display: flex; justify-content: space-between; align-items: center; }
.agent-loading { text-align: center; padding: 24px; }
.agent-status { font-size: 13px; color: #666; margin-top: 8px; }
.platform-skill-meta { margin: 0 0 12px; color: #606266; font-size: 12px; line-height: 1.5; }
.pending-confirmations { margin: 10px 0 14px; padding: 10px 12px; border: 1px solid #f3d19e; border-radius: 8px; background: #fdf6ec; color: #7c5a1b; font-size: 12px; line-height: 1.5; }
.pending-confirmations ul { margin: 6px 0 0; padding-left: 18px; }
.agent-section { margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #eee; }
.agent-section h4 { margin: 0 0 12px; font-size: 15px; }
.input-assessment { padding: 12px; border: 1px solid #e4e7ed; border-radius: 10px; }
.assessment-ready { background: #f0f9eb; border-color: #b3e19d; }
.assessment-needs-input { background: #fdf6ec; border-color: #f3d19e; }
.assessment-title { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.assessment-title h4 { margin-bottom: 8px; }
.assessment-title strong { color: #409eff; }
.assessment-summary { margin: 10px 0; color: #606266; font-size: 12px; line-height: 1.6; }
.assessment-group { display: flex; align-items: center; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.assessment-label { width: 100%; color: #606266; font-size: 12px; font-weight: 600; }
.assessment-questions { margin-top: 12px; color: #303133; font-size: 13px; }
.assessment-questions ol { margin: 6px 0 0; padding-left: 20px; }
.assessment-questions li { margin-bottom: 6px; line-height: 1.5; }
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
.image-scout { margin-top: 16px; padding: 14px; border: 1px solid #d9ecff; border-radius: 10px; background: #f5faff; }
.image-scout-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; margin-bottom: 12px; }
.image-scout-header p { margin: 4px 0 0; color: #606266; font-size: 12px; line-height: 1.5; }
.image-search-message { margin: 10px 0 0; color: #606266; font-size: 12px; }
.image-candidates { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin-top: 12px; }
.image-candidate-card { min-width: 0; overflow: hidden; border: 1px solid #dcdfe6; border-radius: 10px; background: #fff; }
.candidate-thumbnail { width: 100%; aspect-ratio: 1; display: block; object-fit: cover; background: #f5f7fa; }
.candidate-body { display: flex; flex-direction: column; align-items: flex-start; gap: 7px; padding: 10px; }
.candidate-body strong { width: 100%; overflow: hidden; color: #303133; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.candidate-body a { max-width: 100%; overflow: hidden; color: #409eff; font-size: 12px; text-decoration: none; text-overflow: ellipsis; white-space: nowrap; }
.candidate-size { color: #909399; font-size: 11px; }
.candidate-risks { display: flex; flex-wrap: wrap; gap: 4px; }
.candidate-risk-reasons { margin: 0; padding-left: 18px; color: #b26a00; font-size: 12px; line-height: 1.5; }
.publish-blockers { margin-bottom: 16px; }
.publish-blockers ul { margin: 8px 0 0; padding-left: 20px; }
.publish-actions :deep(.el-form-item__content) { display: flex; flex-wrap: wrap; gap: 10px; }
.publish-actions .el-button { margin-left: 0; }
@media (max-width: 1100px) { .image-candidates { grid-template-columns: 1fr; } }

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
.complete-summary.needs-input { color: #e6a23c; }
.cost-stats { font-size: 12px; }
.cost-breakdown { margin-top: 8px; color: #606266; }
.cost-breakdown summary { cursor: pointer; color: #409eff; }
.cost-row { display: flex; justify-content: space-between; gap: 12px; padding: 4px 0; border-bottom: 1px dashed #dcdfe6; }
</style>
