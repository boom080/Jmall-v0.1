<template>
  <div class="store-manager">
    <div class="page-header">
      <h2>🏪 店铺管理</h2>
      <el-button v-if="store" type="success" @click="$router.push(`/store/${store.id}`)">
        👁️ 预览店铺
      </el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- Error State -->
    <el-result
      v-else-if="loadError"
      icon="error"
      title="加载失败"
      :sub-title="loadError"
    >
      <template #extra>
        <el-button type="primary" @click="loadStore">🔄 重新加载</el-button>
      </template>
    </el-result>

    <template v-else-if="store">
      <!-- Store Info -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span>📋 基本信息</span>
          </div>
        </template>

        <el-form :model="form" label-width="100px" label-position="top" class="store-form">
          <el-row :gutter="24">
            <el-col :span="16">
              <el-form-item label="店铺名称">
                <el-input v-model="form.name" maxlength="120" placeholder="给你的店铺起个响亮的名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="经营品类">
                <el-select v-model="form.category" style="width: 100%">
                  <el-option v-for="cat in categories" :key="cat" :value="cat" :label="cat" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="店铺简介">
            <el-input v-model="form.description" type="textarea" :rows="3" maxlength="240"
              placeholder="介绍一下你的店铺特色…" show-word-limit />
          </el-form-item>
        </el-form>
      </el-card>

      <!-- Decoration Config -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="card-header">
            <span>🎨 店铺装修</span>
            <el-button size="small" text @click="resetDecoration">恢复默认</el-button>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :span="12">
            <el-form label-position="top">
              <el-form-item label="主题配色">
                <el-color-picker v-model="decoration.themeColor" show-alpha />
                <span class="color-hint">{{ decoration.themeColor }}</span>
              </el-form-item>
              <el-form-item label="Banner 标题">
                <el-input v-model="decoration.bannerTitle" maxlength="60"
                  placeholder="例：品质好物 · 每日上新" />
              </el-form-item>
              <el-form-item label="Banner 副标题">
                <el-input v-model="decoration.bannerSubtitle" maxlength="120"
                  placeholder="例：全场满99包邮，新用户首单立减" />
              </el-form-item>
            </el-form>
          </el-col>

          <el-col :span="12">
            <div class="preview-card" :style="{ borderColor: decoration.themeColor }">
              <div class="preview-banner" :style="{ background: decoration.themeColor }">
                <h3>{{ decoration.bannerTitle || '品质好物 · 每日上新' }}</h3>
                <p>{{ decoration.bannerSubtitle || '全场满99包邮，新用户首单立减' }}</p>
              </div>
              <div class="preview-body">
                <div class="preview-placeholder">📦</div>
                <p style="color:#999; font-size:13px">商品列表预览</p>
              </div>
            </div>
            <p style="color:#999; font-size:12px; text-align:center; margin-top:8px">
              ⬆️ 店铺首页 Banner 实时预览
            </p>
          </el-col>
        </el-row>
      </el-card>

      <!-- Stats -->
      <el-card shadow="never" class="section-card">
        <template #header>
          <span>📊 店铺数据</span>
        </template>
        <el-row :gutter="24">
          <el-col :span="6">
            <el-statistic title="在售商品" :value="stats.productCount" suffix="件" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="累计销量" :value="stats.totalSales" suffix="件" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="累计订单" :value="stats.totalOrders" suffix="笔" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="创建时间" :value="formatDate(store.createdAt)" />
          </el-col>
        </el-row>
      </el-card>

      <!-- Save -->
      <div class="save-bar">
        <el-button type="primary" size="large" @click="save" :loading="saving">
          💾 保存设置
        </el-button>
      </div>
    </template>

    <!-- Empty state: no store yet -->
    <div v-else-if="!loading" class="no-store">
      <el-card shadow="never" class="section-card">
        <template #header>
          <span>🏪 创建你的店铺</span>
        </template>
        <el-form :model="createForm" label-position="top">
          <el-row :gutter="24">
            <el-col :span="16">
              <el-form-item label="店铺名称" required>
                <el-input v-model="createForm.name" maxlength="120" placeholder="给你的店铺起个响亮的名称" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="经营品类" required>
                <el-select v-model="createForm.category" style="width: 100%" placeholder="选择品类">
                  <el-option v-for="cat in categories" :key="cat" :value="cat" :label="cat" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="店铺简介">
            <el-input v-model="createForm.description" type="textarea" :rows="2" maxlength="240"
              placeholder="介绍一下你的店铺特色…" show-word-limit />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" @click="createStore" :loading="creating">
              🏪 创建店铺
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storeApi } from '@/services/stores'
import type { Store } from '@/types'
import { ElMessage } from 'element-plus'

const categories = [
  '食品饮料', '服饰鞋包', '美妆个护', '手机数码', '家用电器',
  '母婴用品', '运动户外', '图书文娱', '家居家具', '其他',
]

const loading = ref(true)
const loadError = ref<string | null>(null)
const saving = ref(false)
const creating = ref(false)
const store = ref<Store | null>(null)
const stats = reactive({ productCount: 0, totalSales: 0, totalOrders: 0 })

const createForm = reactive({
  name: '',
  category: '',
  description: '',
})

const form = reactive({
  name: '',
  category: '',
  description: '',
})

const defaultDecoration = {
  themeColor: '#FF6B35',
  bannerTitle: '品质好物 · 每日上新',
  bannerSubtitle: '全场满99包邮，新用户首单立减',
}

const decoration = reactive({ ...defaultDecoration })

function resetDecoration() {
  Object.assign(decoration, defaultDecoration)
  ElMessage.success('已恢复默认装修配置')
}

function formatDate(d?: string): string {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

async function loadStore() {
  loading.value = true
  loadError.value = null
  try {
    store.value = await storeApi.getMyStore()
    Object.assign(stats, await storeApi.getMyStats())
    form.name = store.value.name
    form.category = store.value.category
    form.description = store.value.description || ''

    // Parse decoration config
    if (store.value.decorationConfig) {
      try {
        const parsed = typeof store.value.decorationConfig === 'string'
          ? JSON.parse(store.value.decorationConfig)
          : store.value.decorationConfig
        Object.assign(decoration, parsed)
      } catch { /* keep defaults */ }
    }
  } catch (e: any) {
    const msg = e.message || ''
    // "store not found" means user has no store yet — show create form
    if (msg.toLowerCase().includes('store not found') || msg.includes('店铺不存在')) {
      store.value = null
    } else {
      loadError.value = msg || '加载店铺信息失败'
      store.value = null
    }
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    await storeApi.update(store.value!.id, {
      name: form.name,
      category: form.category,
      description: form.description,
      decorationConfig: JSON.stringify({
        themeColor: decoration.themeColor,
        bannerTitle: decoration.bannerTitle,
        bannerSubtitle: decoration.bannerSubtitle,
      }),
    })
    ElMessage.success('✅ 店铺设置已保存')
    await loadStore()
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function createStore() {
  if (!createForm.name || !createForm.category) {
    ElMessage.warning('请填写店铺名称和经营品类')
    return
  }
  creating.value = true
  try {
    await storeApi.create({
      name: createForm.name,
      category: createForm.category,
      description: createForm.description,
    })
    ElMessage.success('🎉 店铺创建成功！')
    await loadStore()
  } catch (e: any) {
    ElMessage.error(e.message || '创建店铺失败')
  } finally {
    creating.value = false
  }
}

onMounted(loadStore)
</script>

<style scoped>
.store-manager {
  padding: 40px;
  max-width: 960px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h2 { margin-bottom: 0; }

.section-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.no-store {
  margin-top: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.store-form {
  margin-top: 8px;
}

.color-hint {
  margin-left: 12px;
  font-size: 13px;
  color: #999;
  font-family: monospace;
}

.preview-card {
  border: 2px solid #eee;
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.3s;
}

.preview-banner {
  padding: 24px 20px;
  color: #fff;
  text-align: center;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.preview-banner h3 {
  margin: 0 0 6px;
  font-size: 18px;
}

.preview-banner p {
  margin: 0;
  font-size: 13px;
  opacity: 0.9;
}

.preview-body {
  padding: 32px;
  text-align: center;
  background: #fafafa;
}

.preview-placeholder {
  font-size: 48px;
  margin-bottom: 8px;
}

.save-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 0;
}

.level-tag {
  margin-left: 4px;
}

.loading-state {
  padding: 24px;
}

h2 {
  margin-bottom: 24px;
}
</style>
