<template>
  <section class="merchant-page-grid merchant-page-grid--single">
    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <div>
            <p class="table-eyebrow">商品管理</p>
            <h2>商品列表与上下架</h2>
          </div>
          <div class="table-header__actions">
            <el-tag>{{ source === 'api' ? '真实接口' : '本地 fallback' }}</el-tag>
            <el-button type="primary" @click="openCreator">新增商品</el-button>
          </div>
        </div>
      </template>

      <el-alert v-if="feedbackError" type="error" :closable="false" class="merchant-alert" :title="feedbackError" />
      <el-alert
        v-if="feedbackSuccess"
        type="success"
        :closable="false"
        class="merchant-alert"
        :title="feedbackSuccess"
      />

      <el-table :data="products" style="width: 100%">
        <el-table-column label="封面" width="110">
          <template #default="{ row }">
            <img :src="row.coverUrl" :alt="row.title" class="table-cover" />
          </template>
        </el-table-column>
        <el-table-column prop="title" label="商品标题" min-width="220" />
        <el-table-column prop="category" label="分类" width="160" />
        <el-table-column label="价格" width="120">
          <template #default="{ row }">¥{{ row.price }}</template>
        </el-table-column>
        <el-table-column label="卖点" min-width="240">
          <template #default="{ row }">
            <el-tag v-for="point in row.sellingPoints" :key="point" class="inline-tag" effect="plain">
              {{ point }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'ready' ? 'success' : 'info'">
              {{ row.status === 'ready' ? '已上架' : '已下架' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <el-button type="primary" text @click="openEditor(row.id)">编辑</el-button>
            <el-button
              :type="row.status === 'ready' ? 'warning' : 'success'"
              text
              :loading="updatingStatus[row.id]"
              @click="handleToggleListing(row)"
            >
              {{ row.status === 'ready' ? '下架' : '上架' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="editorVisible"
      :title="editingId ? '编辑商品' : '新增商品'"
      width="860px"
      destroy-on-close
    >
      <el-alert v-if="feedbackError" type="error" :closable="false" class="merchant-alert" :title="feedbackError" />
      <el-alert
        v-if="feedbackSuccess"
        type="success"
        :closable="false"
        class="merchant-alert"
        :title="feedbackSuccess"
      />

      <el-form label-position="top" @submit.prevent>
        <el-form-item label="商品标题" :error="fieldErrors.title">
          <el-input v-model="form.title" maxlength="120" />
        </el-form-item>
        <el-form-item label="商品分类" :error="fieldErrors.category">
          <el-input v-model="form.category" maxlength="60" placeholder="请输入已存在的后台分类名称" />
        </el-form-item>
        <el-form-item label="价格" :error="fieldErrors.price">
          <el-input v-model="form.price" type="number" min="0" step="0.01" />
        </el-form-item>
        <el-form-item label="卖点" :error="fieldErrors.sellingPoints">
          <el-input v-model="sellingPointsText" type="textarea" :rows="4" placeholder="每行一个卖点" />
        </el-form-item>

        <el-divider content-position="left">AI 文案辅助</el-divider>

        <div class="ai-editor-panel">
          <div class="ai-options-grid">
            <el-form-item label="语气风格" :error="aiFieldErrors.tone">
              <el-select v-model="aiForm.tone">
                <el-option label="专业 professional" value="professional" />
                <el-option label="营销 marketing" value="marketing" />
                <el-option label="温和 warm" value="warm" />
                <el-option label="简洁 concise" value="concise" />
              </el-select>
            </el-form-item>
            <el-form-item label="模型选择" :error="aiFieldErrors.modelName">
              <el-select v-model="aiForm.selectedModelId" placeholder="请选择模型">
                <el-option v-for="item in modelOptions" :key="item.id" :label="item.label" :value="item.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="知识库选择" :error="aiFieldErrors.knowledgeBaseId">
              <el-select v-model="aiForm.knowledgeBaseId" :disabled="knowledgeBaseOptions.length === 0" placeholder="暂无知识库，请先上传 txt 创建">
                <el-option v-for="item in knowledgeBaseOptions" :key="item.id" :label="item.label" :value="item.id" />
              </el-select>
            </el-form-item>
          </div>

          <p v-if="knowledgeBaseOptions.length === 0" class="field-hint">
            暂无知识库，请先到知识库管理页上传 txt 创建。
          </p>
          <p v-if="selectedKnowledgeBase" class="field-hint">
            将带入 {{ selectedKnowledgeBase.documentCount || 0 }} 篇文档 / {{ selectedKnowledgeBase.chunkCount || 0 }} 个 Chunk：
            {{ selectedKnowledgeBase.description || '暂无说明' }}
          </p>

          <el-alert
            v-if="aiError"
            type="error"
            :closable="false"
            show-icon
            class="merchant-alert"
            title="AI 文案生成失败"
            :description="aiError"
          />

          <div class="merchant-actions ai-result-actions">
            <el-button type="primary" :loading="aiSubmitting" :disabled="knowledgeBaseOptions.length === 0" @click="handleGenerateCopy">生成文案</el-button>
            <el-button :disabled="!aiResult || !aiResult.success" @click="applyAiResult">回填标题和卖点</el-button>
          </div>

          <MerchantAiResultPanel v-if="aiResult" :result="aiResult" class="embedded-ai-result" />
          <p v-if="aiResult && !aiResult.success" class="field-hint">
            当前结果是后端降级文案，不会自动覆盖商品字段。
          </p>
        </div>

        <el-form-item label="封面图 URL" :error="fieldErrors.coverUrl">
          <el-input v-model="form.coverUrl" maxlength="255" />
        </el-form-item>
        <el-form-item label="上传商品图片">
          <div class="merchant-upload-row">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="merchant-hidden-input"
              @change="handleFileSelected"
            />
            <div class="merchant-actions merchant-actions--compact">
              <el-button @click="triggerFilePicker" :loading="uploading">选择图片并上传</el-button>
              <span class="merchant-helper-text">
                未配置 OSS 时仍可手动编辑图片 URL；配置项在项目根目录 `.env.local` 的 `JRUNMALL_OSS_*`。
              </span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="状态" :error="fieldErrors.status">
          <el-select v-model="form.status">
            <el-option label="已下架" value="draft" />
            <el-option label="已上架" value="ready" />
          </el-select>
        </el-form-item>
        <el-form-item label="图片预览">
          <img :src="previewCoverUrl" :alt="form.title || '商品封面'" class="table-cover table-cover--large" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="merchant-actions">
          <el-button @click="editorVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">
            {{ editingId ? '保存' : '创建商品' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import MerchantAiResultPanel from '@/components/MerchantAiResultPanel.vue'
import { fetchAiModels, fetchKnowledgeBases, generateMerchantProductCopy, MerchantAiValidationError } from '@/services/merchantAi'
import {
  createMerchantProduct,
  fetchMerchantProductDetail,
  fetchMerchantProducts,
  updateMerchantProduct,
  uploadMerchantProductImage,
} from '@/services/merchantProducts'
import type { MerchantOption, MerchantProduct, MerchantProductUpdatePayload } from '@/types/merchant'
import type { ProductAiResult, ProductAiTone } from '@/types/productAi'

type RouteQuery = Record<string, unknown>

const emptyQuery: RouteQuery = {}
const route = useRoute() as { query?: RouteQuery } | undefined

const products = ref<MerchantProduct[]>([])
const source = ref<'api' | 'fallback'>('fallback')
const editorVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const uploading = ref(false)
const updatingStatus = reactive<Record<number, boolean>>({})
const feedbackError = ref('')
const feedbackSuccess = ref('')
const sellingPointsText = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const fieldErrors = reactive<Record<string, string>>({})

const modelOptions = ref<MerchantOption[]>([])
const knowledgeBaseOptions = ref<MerchantOption[]>([])
const aiResult = ref<ProductAiResult | null>(null)
const aiSubmitting = ref(false)
const aiError = ref('')
const aiFieldErrors = reactive<Record<string, string>>({})
const lastRoutePrefillSignature = ref('')

const form = reactive({
  title: '',
  category: '',
  price: '',
  coverUrl: '',
  status: 'ready' as 'draft' | 'ready',
})

const aiForm = reactive({
  tone: 'professional' as ProductAiTone,
  selectedModelId: '',
  knowledgeBaseId: '',
})

const previewCoverUrl = computed(() => form.coverUrl.trim() || '/placeholders/products/default-product.svg')

const normalizedSellingPoints = computed(() =>
  sellingPointsText.value
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean),
)

const normalizedPrice = computed(() => {
  const value = Number(form.price)
  return Number.isFinite(value) ? value : 0
})

const selectedModel = computed(() => {
  return modelOptions.value.find((item) => item.id === aiForm.selectedModelId) || modelOptions.value[0]
})

const selectedKnowledgeBase = computed(() => {
  return knowledgeBaseOptions.value.find((item) => item.id === aiForm.knowledgeBaseId)
})

onMounted(async () => {
  await Promise.all([loadProducts(), loadAiOptions()])
  applyRoutePrefill(getRouteQuery())
})

watch(
  () => getRouteQuery(),
  (query) => applyRoutePrefill(query),
  { deep: true },
)

async function loadProducts() {
  const result = await fetchMerchantProducts()
  products.value = result.items
  source.value = result.source
}

async function loadAiOptions() {
  modelOptions.value = await fetchAiModels()
  knowledgeBaseOptions.value = await fetchKnowledgeBases()
  ensureAiDefaults()
}

function ensureAiDefaults() {
  const selectedExists = modelOptions.value.some((item) => item.id === aiForm.selectedModelId)
  if (!aiForm.selectedModelId || !selectedExists) {
    aiForm.selectedModelId = pickDefaultModelId(modelOptions.value)
  }
  if (!aiForm.knowledgeBaseId) {
    aiForm.knowledgeBaseId = knowledgeBaseOptions.value[0]?.id || ''
  }
}

function pickDefaultModelId(options: MerchantOption[]) {
  return (
    options.find((item) => item.id.toLowerCase().includes('deepseek'))?.id ||
    options.find((item) => item.provider && item.provider !== 'mock' && !item.id.startsWith('mock:'))?.id ||
    options.find((item) => item.id.startsWith('mock:'))?.id ||
    options[0]?.id ||
    ''
  )
}

function resetFeedback() {
  feedbackError.value = ''
  feedbackSuccess.value = ''
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
}

function resetAiState() {
  aiResult.value = null
  aiError.value = ''
  Object.keys(aiFieldErrors).forEach((key) => delete aiFieldErrors[key])
  aiForm.tone = 'professional'
  ensureAiDefaults()
}

function resetForm() {
  editingId.value = null
  form.title = ''
  form.category = ''
  form.price = ''
  form.coverUrl = ''
  form.status = 'ready'
  sellingPointsText.value = ''
}

function openCreator(prefill: Partial<MerchantProduct & { knowledgeBaseId: string; sellingPointsText: string }> = {}) {
  resetFeedback()
  resetForm()
  resetAiState()
  form.title = prefill.title || ''
  form.category = prefill.category || ''
  form.price = prefill.price === undefined ? '' : String(prefill.price)
  form.coverUrl = prefill.coverUrl || ''
  form.status = prefill.status || 'ready'
  sellingPointsText.value = prefill.sellingPointsText || prefill.sellingPoints?.join('\n') || ''
  if (prefill.knowledgeBaseId) {
    aiForm.knowledgeBaseId = prefill.knowledgeBaseId
  }
  editorVisible.value = true
}

function triggerFilePicker() {
  fileInput.value?.click()
}

async function handleFileSelected(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }
  resetFeedback()
  uploading.value = true
  try {
    const uploaded = await uploadMerchantProductImage(file)
    form.coverUrl = uploaded.url
    feedbackSuccess.value = '图片上传成功，已自动回填封面图地址'
  } catch (error) {
    feedbackError.value = error instanceof Error ? error.message : '图片上传失败'
  } finally {
    uploading.value = false
    target.value = ''
  }
}

async function openEditor(id: number) {
  resetFeedback()
  resetAiState()
  try {
    const detail = await fetchMerchantProductDetail(id)
    editingId.value = id
    form.title = detail.title
    form.category = detail.category
    form.price = String(detail.price)
    form.coverUrl = detail.coverUrl
    form.status = detail.status
    sellingPointsText.value = detail.sellingPoints.join('\n')
    editorVisible.value = true
  } catch (error) {
    feedbackError.value = error instanceof Error ? error.message : '商品详情加载失败'
  }
}

function validateForm() {
  resetFeedback()
  if (!form.title.trim()) {
    fieldErrors.title = '商品标题不能为空'
  }
  if (!form.category.trim()) {
    fieldErrors.category = '商品分类不能为空'
  }
  if (normalizedPrice.value < 0) {
    fieldErrors.price = '商品价格不能小于 0'
  }
  if (normalizedSellingPoints.value.length > 8) {
    fieldErrors.sellingPoints = '卖点不能超过 8 条'
  }
  if (form.coverUrl.trim().length > 255) {
    fieldErrors.coverUrl = '商品封面地址不能超过 255 个字符'
  }
  if (!['draft', 'ready'].includes(form.status)) {
    fieldErrors.status = '商品状态非法'
  }
  if (Object.keys(fieldErrors).length > 0) {
    feedbackError.value = Object.values(fieldErrors).join('；')
    return false
  }
  return true
}

function buildPayload(): MerchantProductUpdatePayload {
  return {
    title: form.title.trim(),
    category: form.category.trim(),
    price: normalizedPrice.value,
    sellingPoints: normalizedSellingPoints.value,
    coverUrl: form.coverUrl.trim(),
    status: form.status,
  }
}

async function handleSave() {
  if (!validateForm()) {
    return
  }

  saving.value = true
  try {
    const payload = buildPayload()
    if (editingId.value) {
      const updated = await updateMerchantProduct(editingId.value, payload)
      products.value = products.value.map((item) => (item.id === updated.id ? updated : item))
      feedbackSuccess.value = '商品已保存'
    } else {
      const created = await createMerchantProduct(payload)
      products.value = [created, ...products.value.filter((item) => item.id !== created.id)]
      editingId.value = created.id
      feedbackSuccess.value = '商品已新增'
    }
  } catch (error) {
    feedbackError.value = error instanceof Error ? error.message : '商品保存失败'
  } finally {
    saving.value = false
  }
}

async function handleGenerateCopy() {
  aiError.value = ''
  Object.keys(aiFieldErrors).forEach((key) => delete aiFieldErrors[key])
  if (knowledgeBaseOptions.value.length === 0) {
    aiFieldErrors.knowledgeBaseId = '暂无知识库，请先上传 txt 创建'
    aiError.value = aiFieldErrors.knowledgeBaseId
    return
  }
  aiSubmitting.value = true
  try {
    const selectedModelId = selectedModel.value?.id || 'mock:mock-product-copy-v1'
    const [provider, ...modelParts] = selectedModelId.split(':')
    aiResult.value = await generateMerchantProductCopy({
      title: form.title.trim(),
      category: form.category.trim(),
      sellingPoints: normalizedSellingPoints.value,
      tone: aiForm.tone,
      modelProvider: provider,
      modelName: modelParts.join(':') || selectedModelId,
      knowledgeBaseId: aiForm.knowledgeBaseId || undefined,
    })
  } catch (error) {
    aiResult.value = null
    if (error instanceof MerchantAiValidationError) {
      Object.assign(aiFieldErrors, error.fieldErrors)
      if (error.fieldErrors.title) {
        fieldErrors.title = error.fieldErrors.title
      }
      if (error.fieldErrors.category) {
        fieldErrors.category = error.fieldErrors.category
      }
      if (error.fieldErrors.sellingPoints) {
        fieldErrors.sellingPoints = error.fieldErrors.sellingPoints
      }
      aiError.value = Object.values(error.fieldErrors).join('；') || error.message
      return
    }
    aiError.value = error instanceof Error ? error.message : '商品 AI 请求失败'
  } finally {
    aiSubmitting.value = false
  }
}

function applyAiResult() {
  if (!aiResult.value || !aiResult.value.success) {
    aiError.value = '当前没有可回填的成功 AI 结果'
    return
  }
  form.title = aiResult.value.generatedTitle.trim() || form.title
  if (aiResult.value.highlights.length > 0) {
    sellingPointsText.value = aiResult.value.highlights.join('\n')
  }
  feedbackSuccess.value = 'AI 文案已回填到当前商品表单'
}

async function handleToggleListing(row: MerchantProduct) {
  resetFeedback()
  updatingStatus[row.id] = true
  try {
    const nextStatus = row.status === 'ready' ? 'draft' : 'ready'
    const updated = await updateMerchantProduct(row.id, {
      title: row.title,
      category: row.category,
      price: row.price,
      sellingPoints: row.sellingPoints,
      coverUrl: row.coverUrl,
      status: nextStatus,
    })
    products.value = products.value.map((item) => (item.id === updated.id ? updated : item))
    feedbackSuccess.value = nextStatus === 'ready' ? '商品已上架' : '商品已下架'
  } catch (error) {
    feedbackError.value = error instanceof Error ? error.message : '商品上下架失败'
  } finally {
    updatingStatus[row.id] = false
  }
}

function getRouteQuery() {
  return route?.query || emptyQuery
}

function applyRoutePrefill(query: RouteQuery) {
  const knowledgeBaseId = queryValue(query.knowledgeBaseId)
  const title = queryValue(query.title)
  const category = queryValue(query.category)
  const sellingPointsTextValue = queryValue(query.sellingPoints)
  const mode = queryValue(query.mode)
  const signature = JSON.stringify({ knowledgeBaseId, title, category, sellingPointsTextValue, mode })
  if (signature === lastRoutePrefillSignature.value) {
    return
  }
  lastRoutePrefillSignature.value = signature
  if (mode !== 'create' && !knowledgeBaseId && !title && !category && !sellingPointsTextValue) {
    return
  }
  openCreator({
    title,
    category,
    knowledgeBaseId,
    sellingPointsText: sellingPointsTextValue,
  })
}

function queryValue(value: unknown) {
  const raw = Array.isArray(value) ? value[0] : value
  return raw === undefined || raw === null ? '' : String(raw)
}
</script>

<style scoped>
.table-header__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-editor-panel {
  margin-bottom: 18px;
  padding: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  background: #f8fafc;
}

.ai-options-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.field-hint {
  margin: 4px 0 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.ai-result-actions {
  margin-bottom: 14px;
}

.embedded-ai-result {
  margin-top: 12px;
}

.merchant-upload-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.merchant-hidden-input {
  display: none;
}

.merchant-helper-text {
  color: #6b7280;
  font-size: 12px;
  line-height: 1.5;
}

.merchant-actions--compact {
  align-items: center;
}

.table-cover--large {
  width: 160px;
  height: 120px;
}

@media (max-width: 960px) {
  .ai-options-grid,
  .table-header__actions {
    display: block;
  }

  .table-header__actions > * {
    margin-top: 8px;
  }
}
</style>
