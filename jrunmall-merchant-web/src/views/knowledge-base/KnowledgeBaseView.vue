<template>
  <section class="merchant-page-grid merchant-page-grid--wide">
    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <div>
            <p class="table-eyebrow">知识库 / RAG</p>
            <h2>上传 txt 创建真实知识库</h2>
          </div>
          <el-tag type="success">txt / pgvector RAG</el-tag>
        </div>
      </template>

      <el-form label-position="top" class="merchant-inline-form" @submit.prevent>
        <el-form-item label="知识库名称" :error="txtUploadErrors.name">
          <el-input v-model="txtUploadForm.name" maxlength="80" placeholder="例如：手机运营文案知识库" />
        </el-form-item>
        <el-form-item label="知识库说明" :error="txtUploadErrors.description">
          <el-input v-model="txtUploadForm.description" maxlength="240" placeholder="说明该知识库的用途与适用场景" />
        </el-form-item>
        <el-form-item label="txt 文件" :error="txtUploadErrors.file">
          <div class="merchant-upload-row">
            <input
              ref="txtFileInput"
              type="file"
              accept="text/plain,.txt"
              class="merchant-hidden-input"
              @change="handleTxtFileSelected"
            />
            <div class="merchant-actions merchant-actions--compact">
              <el-button @click="triggerTxtPicker">选择 txt</el-button>
              <span class="merchant-helper-text">{{ selectedTxtFileName || '未选择文件' }}</span>
            </div>
          </div>
        </el-form-item>
        <div class="merchant-actions">
          <el-button type="primary" :loading="txtUploading" @click="handleTxtUpload">上传 txt 创建知识库</el-button>
          <span v-if="txtUploadMessage" class="inline-message">{{ txtUploadMessage }}</span>
        </div>
      </el-form>

      <el-divider />

      <el-form label-position="top" class="merchant-inline-form" @submit.prevent>
        <el-form-item label="知识库名称" :error="createErrors.name">
          <el-input v-model="createForm.name" maxlength="80" placeholder="例如：手机运营文案知识库" />
        </el-form-item>
        <el-form-item label="知识库说明" :error="createErrors.description">
          <el-input v-model="createForm.description" maxlength="240" placeholder="说明该知识库的用途与适用场景" />
        </el-form-item>
        <div class="merchant-actions">
          <el-button type="primary" :loading="creating" @click="handleCreate">新增知识库</el-button>
          <span v-if="createMessage" class="inline-message">{{ createMessage }}</span>
        </div>
      </el-form>

      <el-table :data="knowledgeBases" style="width: 100%; margin-top: 16px">
        <el-table-column prop="label" label="知识库名称" min-width="220" />
        <el-table-column prop="description" label="说明" min-width="220" />
        <el-table-column prop="documentCount" label="文档数" width="100" />
        <el-table-column prop="chunkCount" label="Chunk 数" width="110" />
        <el-table-column prop="embeddingStatus" label="Embedding 状态" min-width="160" />
        <el-table-column prop="updatedAt" label="最近更新" min-width="180" />
        <el-table-column label="动作" width="220">
          <template #default="{ row }">
            <el-button type="primary" text @click="selectKnowledgeBase(row.id)">查看文档</el-button>
            <el-button type="success" text @click="openProductCreator(row.id)">新增商品</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="knowledgeBases.length === 0" description="暂无知识库，请上传 txt 创建" />
    </el-card>

    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <div>
            <p class="table-eyebrow">文档导入</p>
            <h2>{{ selectedKnowledgeBaseLabel || '请选择知识库' }}</h2>
          </div>
          <el-tag v-if="selectedKnowledgeBaseId">{{ selectedKnowledgeBaseId }}</el-tag>
        </div>
      </template>

      <el-empty
        v-if="!selectedKnowledgeBaseId"
        description="先从上方知识库列表中选择一个知识库，再导入文本或 PDF；导入完成后可在新增或编辑商品时选择该知识库生成文案。"
      />

      <template v-else>
        <el-form label-position="top" @submit.prevent>
          <el-form-item label="文本标题" :error="importErrors.title">
            <el-input v-model="importForm.title" maxlength="120" placeholder="例如：新品手机卖点资料" />
          </el-form-item>
          <el-form-item label="文本内容" :error="importErrors.content">
            <el-input
              v-model="importForm.content"
              type="textarea"
              :rows="8"
              maxlength="8000"
              placeholder="直接粘贴一段可用于 RAG 的商品知识文本。"
            />
          </el-form-item>
          <div class="merchant-actions">
            <el-button type="primary" :loading="importing" @click="handleImport">导入文本并切块/Embedding</el-button>
            <el-button type="success" :disabled="!lastImportedDocument" @click="applyImportedDocumentToProduct">用刚导入文档新增商品</el-button>
            <span v-if="importMessage" class="inline-message">{{ importMessage }}</span>
          </div>
        </el-form>

        <el-divider />

        <el-form label-position="top" @submit.prevent>
          <el-form-item label="PDF 标题" :error="pdfErrors.title">
            <el-input v-model="pdfForm.title" maxlength="120" placeholder="默认使用 PDF 文件名" />
          </el-form-item>
          <el-form-item label="PDF 文件" :error="pdfErrors.file">
            <div class="merchant-upload-row">
              <input
                ref="pdfFileInput"
                type="file"
                accept="application/pdf,.pdf"
                class="merchant-hidden-input"
                @change="handlePdfFileSelected"
              />
              <div class="merchant-actions merchant-actions--compact">
                <el-button @click="triggerPdfPicker">选择 PDF</el-button>
                <span class="merchant-helper-text">{{ selectedPdfFileName || '未选择文件' }}</span>
              </div>
            </div>
          </el-form-item>
          <div class="merchant-actions">
            <el-button type="primary" :loading="pdfImporting" @click="handlePdfImport">导入 PDF 并切块/Embedding</el-button>
            <span v-if="pdfMessage" class="inline-message">{{ pdfMessage }}</span>
          </div>
        </el-form>

        <el-table :data="documents" style="width: 100%; margin-top: 16px">
          <el-table-column prop="title" label="文档标题" min-width="200" />
          <el-table-column prop="contentPreview" label="内容预览" min-width="280" />
          <el-table-column prop="chunkCount" label="Chunk 数" width="110" />
          <el-table-column prop="embeddingStatus" label="Embedding 状态" min-width="160" />
          <el-table-column prop="updatedAt" label="最近更新" min-width="180" />
        </el-table>
      </template>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import {
  createMerchantKnowledgeBase,
  fetchKnowledgeBaseDocuments,
  fetchMerchantKnowledgeBases,
  importKnowledgeBasePdfDocument,
  importKnowledgeBaseTextDocument,
  uploadTxtCreateKnowledgeBase,
} from '@/services/merchantKnowledgeBases'
import type {
  MerchantKnowledgeBase,
  MerchantKnowledgeBaseDocument,
} from '@/types/merchant'

const router = useRouter()

const knowledgeBases = ref<MerchantKnowledgeBase[]>([])
const documents = ref<MerchantKnowledgeBaseDocument[]>([])
const selectedKnowledgeBaseId = ref('')
const creating = ref(false)
const importing = ref(false)
const pdfImporting = ref(false)
const createMessage = ref('')
const importMessage = ref('')
const pdfMessage = ref('')
const lastImportedDocument = ref<MerchantKnowledgeBaseDocument | null>(null)
const lastImportedContent = ref('')
const pdfFileInput = ref<HTMLInputElement | null>(null)
const txtFileInput = ref<HTMLInputElement | null>(null)
const selectedPdfFile = ref<File | null>(null)
const selectedPdfFileName = ref('')
const selectedTxtFile = ref<File | null>(null)
const selectedTxtFileName = ref('')
const txtUploading = ref(false)
const txtUploadMessage = ref('')

const createForm = reactive({
  name: '',
  description: '',
})

const txtUploadForm = reactive({
  name: '',
  description: '',
})

const importForm = reactive({
  title: '',
  content: '',
})

const pdfForm = reactive({
  title: '',
})

const createErrors = reactive<Record<string, string>>({})
const importErrors = reactive<Record<string, string>>({})
const pdfErrors = reactive<Record<string, string>>({})
const txtUploadErrors = reactive<Record<string, string>>({})

const selectedKnowledgeBaseLabel = computed(() => {
  return knowledgeBases.value.find((item) => item.id === selectedKnowledgeBaseId.value)?.label || ''
})

function resetErrors(target: Record<string, string>) {
  Object.keys(target).forEach((key) => delete target[key])
}

async function loadKnowledgeBases() {
  knowledgeBases.value = await fetchMerchantKnowledgeBases()
  if (!selectedKnowledgeBaseId.value && knowledgeBases.value[0]) {
    selectedKnowledgeBaseId.value = knowledgeBases.value[0].id
    await loadDocuments(selectedKnowledgeBaseId.value)
  } else if (knowledgeBases.value.length === 0) {
    selectedKnowledgeBaseId.value = ''
    documents.value = []
  }
}

async function loadDocuments(knowledgeBaseId: string) {
  documents.value = await fetchKnowledgeBaseDocuments(knowledgeBaseId)
}

async function selectKnowledgeBase(knowledgeBaseId: string) {
  selectedKnowledgeBaseId.value = knowledgeBaseId
  importMessage.value = ''
  pdfMessage.value = ''
  lastImportedDocument.value = null
  lastImportedContent.value = ''
  selectedPdfFile.value = null
  selectedPdfFileName.value = ''
  await loadDocuments(knowledgeBaseId)
}

function openProductCreator(knowledgeBaseId: string) {
  router.push({
    name: 'products',
    query: {
      mode: 'create',
      knowledgeBaseId,
    },
  })
}

function applyImportedDocumentToProduct() {
  if (!selectedKnowledgeBaseId.value || !lastImportedDocument.value) {
    return
  }
  router.push({
    name: 'products',
    query: {
      mode: 'create',
      knowledgeBaseId: selectedKnowledgeBaseId.value,
      title: lastImportedDocument.value.title,
      category: selectedKnowledgeBaseLabel.value || '知识库商品',
      sellingPoints: lastImportedContent.value
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 5)
        .join('\n'),
    },
  })
}

async function handleCreate() {
  resetErrors(createErrors)
  createMessage.value = ''
  if (!createForm.name.trim()) {
    createErrors.name = '知识库名称不能为空'
    return
  }

  creating.value = true
  try {
    const knowledgeBase = await createMerchantKnowledgeBase({
      name: createForm.name.trim(),
      description: createForm.description.trim(),
    })
    createMessage.value = `知识库已创建：${knowledgeBase.label}`
    createForm.name = ''
    createForm.description = ''
    await loadKnowledgeBases()
    await selectKnowledgeBase(knowledgeBase.id)
  } catch (error) {
    createMessage.value = error instanceof Error ? error.message : '知识库创建失败'
  } finally {
    creating.value = false
  }
}

function triggerTxtPicker() {
  txtFileInput.value?.click()
}

function handleTxtFileSelected(event: Event) {
  resetErrors(txtUploadErrors)
  txtUploadMessage.value = ''
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] || null
  selectedTxtFile.value = file
  selectedTxtFileName.value = file ? file.name : ''
}

async function handleTxtUpload() {
  resetErrors(txtUploadErrors)
  txtUploadMessage.value = ''
  if (!txtUploadForm.name.trim()) {
    txtUploadErrors.name = '知识库名称不能为空'
  }
  if (!selectedTxtFile.value) {
    txtUploadErrors.file = '请选择 txt 文件'
  } else if (!selectedTxtFile.value.name.toLowerCase().endsWith('.txt')) {
    txtUploadErrors.file = '仅支持 txt 文件'
  } else if (selectedTxtFile.value.size > 2 * 1024 * 1024) {
    txtUploadErrors.file = 'txt 文件不能超过 2MB'
  }
  if (Object.keys(txtUploadErrors).length > 0) {
    return
  }

  txtUploading.value = true
  try {
    const result = await uploadTxtCreateKnowledgeBase({
      name: txtUploadForm.name.trim(),
      description: txtUploadForm.description.trim(),
      file: selectedTxtFile.value as File,
    })
    txtUploadMessage.value = `已创建知识库：${result.name}，Chunk 数：${result.chunkCount}`
    txtUploadForm.name = ''
    txtUploadForm.description = ''
    selectedTxtFile.value = null
    selectedTxtFileName.value = ''
    if (txtFileInput.value) {
      txtFileInput.value.value = ''
    }
    await loadKnowledgeBases()
    await selectKnowledgeBase(result.knowledgeBaseId)
  } catch (error) {
    txtUploadMessage.value = error instanceof Error ? error.message : 'txt 上传创建知识库失败'
  } finally {
    txtUploading.value = false
  }
}

async function handleImport() {
  resetErrors(importErrors)
  importMessage.value = ''

  if (!selectedKnowledgeBaseId.value) {
    importErrors.title = '请先选择知识库'
    return
  }
  if (!importForm.title.trim()) {
    importErrors.title = '文本标题不能为空'
  }
  if (!importForm.content.trim()) {
    importErrors.content = '文本内容不能为空'
  }
  if (Object.keys(importErrors).length > 0) {
    return
  }

  importing.value = true
  try {
    const document = await importKnowledgeBaseTextDocument(selectedKnowledgeBaseId.value, {
      title: importForm.title.trim(),
      content: importForm.content.trim(),
    })
    importMessage.value = `已导入文本：${document.title}`
    lastImportedDocument.value = document
    lastImportedContent.value = importForm.content.trim()
    importForm.title = ''
    importForm.content = ''
    await loadKnowledgeBases()
    await loadDocuments(selectedKnowledgeBaseId.value)
  } catch (error) {
    importMessage.value = error instanceof Error ? error.message : '文本导入失败'
  } finally {
    importing.value = false
  }
}

function triggerPdfPicker() {
  pdfFileInput.value?.click()
}

function handlePdfFileSelected(event: Event) {
  resetErrors(pdfErrors)
  pdfMessage.value = ''
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] || null
  selectedPdfFile.value = file
  selectedPdfFileName.value = file ? file.name : ''
}

async function handlePdfImport() {
  resetErrors(pdfErrors)
  pdfMessage.value = ''

  if (!selectedKnowledgeBaseId.value) {
    pdfErrors.file = '请先选择知识库'
    return
  }
  if (!selectedPdfFile.value) {
    pdfErrors.file = '请选择 PDF 文件'
    return
  }
  if (selectedPdfFile.value.type && selectedPdfFile.value.type !== 'application/pdf') {
    pdfErrors.file = '仅支持 PDF 文件'
    return
  }
  if (selectedPdfFile.value.size > 10 * 1024 * 1024) {
    pdfErrors.file = 'PDF 文件不能超过 10MB'
    return
  }

  pdfImporting.value = true
  try {
    const document = await importKnowledgeBasePdfDocument(selectedKnowledgeBaseId.value, {
      title: pdfForm.title.trim() || selectedPdfFile.value.name,
      file: selectedPdfFile.value,
    })
    pdfMessage.value = `已导入 PDF：${document.title}`
    lastImportedDocument.value = document
    lastImportedContent.value = document.contentPreview
    pdfForm.title = ''
    selectedPdfFile.value = null
    selectedPdfFileName.value = ''
    if (pdfFileInput.value) {
      pdfFileInput.value.value = ''
    }
    await loadKnowledgeBases()
    await loadDocuments(selectedKnowledgeBaseId.value)
  } catch (error) {
    pdfMessage.value = error instanceof Error ? error.message : 'PDF 导入失败'
  } finally {
    pdfImporting.value = false
  }
}

onMounted(loadKnowledgeBases)
</script>

<style scoped>
.merchant-inline-form {
  display: grid;
  gap: 12px;
}

.inline-message {
  color: var(--el-text-color-regular);
  font-size: 14px;
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
</style>


