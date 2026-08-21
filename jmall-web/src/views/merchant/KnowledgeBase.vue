<template>
  <div class="knowledge-base">
    <div class="page-header">
      <h2>📚 知识库管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon> 新建知识库
      </el-button>
    </div>

    <p class="subtitle">上传行业资料、产品手册等文档，AI 将基于这些知识生成更精准的商品文案。</p>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- Error State -->
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadKnowledgeBases">🔄 重新加载</el-button>
      </template>
    </el-result>

    <!-- Empty State -->
    <div v-else-if="knowledgeBases.length === 0" class="empty-state">
      <el-empty description="还没有知识库">
        <el-button type="primary" @click="showCreateDialog = true">📝 创建第一个知识库</el-button>
      </el-empty>
    </div>

    <!-- KB List -->
    <div v-else class="kb-grid">
      <div v-for="kb in knowledgeBases" :key="kb.id" class="kb-card">
        <div class="kb-header">
          <h3>{{ kb.name || kb.label }}</h3>
          <el-dropdown trigger="click" @command="(cmd: string) => handleKbCommand(cmd, kb)">
            <el-button size="small" circle>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="view">📄 查看文档</el-dropdown-item>
                <el-dropdown-item command="upload">📝 添加文本</el-dropdown-item>
                <el-dropdown-item command="delete" divided>🗑️ 删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <p class="kb-desc">{{ kb.description || '暂无描述' }}</p>
        <div class="kb-stats">
          <el-tag size="small" type="info">{{ kb.documentCount || 0 }} 个文档</el-tag>
          <el-tag size="small" type="info">{{ kb.chunkCount || 0 }} 个分块</el-tag>
          <el-tag v-if="kb.embeddingStatus" size="small" :type="isIndexed(kb.embeddingStatus) ? 'success' : 'warning'">
            {{ isIndexed(kb.embeddingStatus) ? '已索引' : (kb.embeddingStatus === 'empty' ? '暂无索引' : '索引中') }}
          </el-tag>
        </div>
      </div>
    </div>

    <!-- Create KB Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建知识库" width="500px">
      <el-form :model="createForm" label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="createForm.name" placeholder="如：茶叶行业知识" maxlength="60" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="createForm.description" type="textarea" :rows="3" placeholder="描述知识库的内容和用途" maxlength="200" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createKnowledgeBase" :loading="creating">创建</el-button>
      </template>
    </el-dialog>

    <!-- Import pasted text dialog -->
    <el-dialog v-model="showUploadDialog" title="添加文本资料" width="500px">
      <el-form label-position="top">
        <el-form-item label="知识库">
          <el-input :model-value="selectedKb?.name || selectedKb?.label" disabled />
        </el-form-item>
        <el-form-item label="文档标题" required>
          <el-input v-model="uploadTitle" placeholder="如：产品卖点与使用说明" maxlength="120" />
        </el-form-item>
        <el-form-item label="文档内容" required>
          <el-input v-model="uploadContent" type="textarea" :rows="10" maxlength="8000" show-word-limit placeholder="粘贴或输入段落内容..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="uploadTxt" :loading="uploading">添加</el-button>
      </template>
    </el-dialog>

    <!-- Documents Dialog -->
    <el-dialog v-model="showDocsDialog" :title="`${selectedKb?.name || selectedKb?.label} - 文档列表`" width="600px">
      <div v-if="documentsLoading" class="loading-state">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else-if="documents.length === 0" class="empty-state">
        <el-empty description="该知识库还没有文档">
          <el-button type="primary" @click="showDocsDialog = false; showUploadDialog = true">📤 上传第一篇文档</el-button>
        </el-empty>
      </div>
      <el-table v-else :data="documents" stripe>
        <el-table-column prop="title" label="文档名" />
        <el-table-column prop="sourceFilename" label="源文件" />
        <el-table-column prop="chunkCount" label="分块数" width="80" />
        <el-table-column prop="createdAt" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showDocsDialog = false">关闭</el-button>
        <el-button type="primary" @click="showDocsDialog = false; showUploadDialog = true">📤 上传文档</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/services/http'

interface KnowledgeBase {
  id: string
  name?: string
  label?: string
  description?: string
  documentCount?: number
  chunkCount?: number
  embeddingStatus?: string
}

interface KbDocument {
  id: string
  title: string
  sourceFilename: string
  chunkCount: number
  createdAt: string
}

const loading = ref(false)
const error = ref<string | null>(null)
const creating = ref(false)
const uploading = ref(false)
const documentsLoading = ref(false)

const knowledgeBases = ref<KnowledgeBase[]>([])
const documents = ref<KbDocument[]>([])

const showCreateDialog = ref(false)
const showUploadDialog = ref(false)
const showDocsDialog = ref(false)
const selectedKb = ref<KnowledgeBase | null>(null)

const createForm = reactive({ name: '', description: '' })
const uploadTitle = ref('')
const uploadContent = ref('')

function formatDate(d: string) {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

function isIndexed(status?: string) {
  return status === 'completed' || status === 'ready' || String(status || '').startsWith('embedded:')
}

async function loadKnowledgeBases() {
  loading.value = true
  error.value = null
  try {
    knowledgeBases.value = await http.get('/ai/knowledge-bases')
  } catch (e: any) {
    error.value = e.message || '加载知识库列表失败'
    knowledgeBases.value = []
  } finally {
    loading.value = false
  }
}

async function createKnowledgeBase() {
  if (!createForm.name.trim()) {
    ElMessage.warning('请输入知识库名称')
    return
  }
  creating.value = true
  try {
    const created: any = await http.post('/ai/knowledge-bases', {
      name: createForm.name.trim(),
      description: createForm.description.trim(),
    })
    ElMessage.success(created?.embeddingStatus === 'existing' ? '同名知识库已存在，未重复创建' : '知识库创建成功')
    showCreateDialog.value = false
    createForm.name = ''
    createForm.description = ''
    await loadKnowledgeBases()
  } catch (e: any) {
    ElMessage.error(e.message || '创建失败')
  } finally {
    creating.value = false
  }
}

async function uploadTxt() {
  if (!selectedKb.value?.id) {
    ElMessage.error('请先选择知识库')
    return
  }
  if (!uploadTitle.value.trim()) {
    ElMessage.warning('请输入文档标题')
    return
  }
  if (!uploadContent.value.trim()) {
    ElMessage.warning('请输入文档内容')
    return
  }
  uploading.value = true
  try {
    await http.post('/ai/knowledge-bases/upload-txt', {
      kbId: selectedKb.value?.id,
      title: uploadTitle.value.trim(),
      content: uploadContent.value.trim(),
    })
    ElMessage.success('文本资料添加成功')
    showUploadDialog.value = false
    uploadTitle.value = ''
    uploadContent.value = ''
    await loadKnowledgeBases()
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function loadDocuments(kbId: string) {
  documentsLoading.value = true
  try {
    documents.value = await http.get(`/ai/knowledge-bases/${kbId}/documents`)
  } catch {
    documents.value = []
  } finally {
    documentsLoading.value = false
  }
}

async function deleteKnowledgeBase(kb: KnowledgeBase) {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库「${kb.name || kb.label}」吗？所有文档和索引将被永久删除。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    await http.delete(`/ai/knowledge-bases/${kb.id}`)
    ElMessage.success('知识库已删除')
    await loadKnowledgeBases()
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.message || '删除失败')
    }
  }
}

function handleKbCommand(command: string, kb: KnowledgeBase) {
  selectedKb.value = kb
  switch (command) {
    case 'view':
      showDocsDialog.value = true
      loadDocuments(kb.id)
      break
    case 'upload':
      showUploadDialog.value = true
      break
    case 'delete':
      deleteKnowledgeBase(kb)
      break
  }
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-base { padding: 24px; max-width: 1200px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.page-header h2 { margin: 0; }
.subtitle { color: #999; margin-bottom: 24px; font-size: 14px; }
.kb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.kb-card {
  background: white; border-radius: 16px; padding: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: box-shadow 0.2s;
}
.kb-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
.kb-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.kb-header h3 { margin: 0; font-size: 17px; }
.kb-desc { color: #666; font-size: 14px; margin-bottom: 16px; min-height: 40px; }
.kb-stats { display: flex; gap: 6px; flex-wrap: wrap; }
.loading-state { padding: 24px 0; }
.empty-state { padding: 60px 0; }
</style>
