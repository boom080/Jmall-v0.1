<template>
  <div class="product-feed">
    <!-- Hero Filter Area -->
    <div class="hero-filter">
      <div class="hero-content">
        <h2 class="hero-title">发现好物</h2>
        <div class="hero-search">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索商品名称、副标题、描述..."
            clearable
            size="large"
            @keyup.enter="onSearch"
            @clear="onSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
            <template #append>
              <el-button @click="onSearch" :loading="loading" style="background: #409eff; color: #fff; border: none;">
                <el-icon><Search /></el-icon> 搜索
              </el-button>
            </template>
          </el-input>
        </div>
        <div class="hero-styles">
          <el-radio-group v-model="activeStyle" @change="loadProducts" size="default">
            <el-radio-button value="all">🏠 全部</el-radio-button>
            <el-radio-button value="pinduoduo">🔴 拼多多风</el-radio-button>
            <el-radio-button value="taobao">🟠 淘宝风</el-radio-button>
            <el-radio-button value="jd">🔴 京东风</el-radio-button>
            <el-radio-button value="suning">🔵 苏宁风</el-radio-button>
            <el-radio-button value="xiaohongshu">💗 小红书风</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- Error -->
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadProducts">🔄 重新加载</el-button>
      </template>
    </el-result>

    <!-- Product Grid -->
    <div v-else class="product-grid" :class="`style-${activeStyle}`">
      <div
        v-for="product in products"
        :key="product.id"
        class="product-card"
        :class="`card-style-${product.style}`"
        @click="viewDetail(product.id)"
      >
        <div class="card-image">
          <img
            :src="getProductImage(product.images, product.category)"
            :alt="product.title"
          />
          <span class="style-tag">{{ styleLabel(product.style) }}</span>
        </div>
        <div class="card-body">
          <h3 class="card-title">{{ product.title }}</h3>
          <p v-if="product.subtitle" class="card-subtitle">{{ product.subtitle }}</p>
          <p v-if="descriptionPreview(product)" class="card-summary">{{ descriptionPreview(product) }}</p>
          <div v-if="sellingPoints(product).length" class="card-highlights">
            <span v-for="point in sellingPoints(product).slice(0, 2)" :key="point">{{ point }}</span>
          </div>
          <div class="card-meta">
            <span class="card-category">{{ product.category }}</span>
            <span>👁 {{ product.viewCount || 0 }}</span>
            <span>📦 {{ product.saleCount || 0 }} 已售</span>
          </div>
          <p v-if="product.storeName" class="card-store">🏪 {{ product.storeName }}</p>
          <div class="card-footer">
            <span class="card-price">¥{{ formatPrice(product.price) }}</span>
            <span class="view-detail">查看详情 →</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <el-empty v-if="!loading && products.length === 0" description="还没有商品，去商家中心上架第一个吧！">
      <el-button type="primary" @click="$router.push('/merchant/products')">🏪 去上架</el-button>
    </el-empty>

    <!-- Pagination -->
    <div class="pagination" v-if="total > pageSize">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { productApi } from '@/services/products'
import { getProductImage } from '@/services/imageUtils'
import type { Product } from '@/types'

const router = useRouter()

const products = ref<Product[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const activeStyle = ref('all')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)

const STYLE_LABELS: Record<string, string> = {
  pinduoduo: '拼多多风', taobao: '淘宝风', jd: '京东风',
  suning: '苏宁风', xiaohongshu: '小红书风',
}

function styleLabel(style: string) { return STYLE_LABELS[style] || '' }

function formatPrice(price: number): string {
  return (price / 100).toFixed(2)
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

async function loadProducts() {
  loading.value = true
  error.value = null
  try {
    const params: any = { page: currentPage.value, size: pageSize.value, status: 'published' }
    if (activeStyle.value !== 'all') params.style = activeStyle.value
    if (searchKeyword.value.trim()) params.keyword = searchKeyword.value.trim()
    const result: any = await productApi.list(params)
    products.value = result.records || result.items || []
    total.value = result.total || 0
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
  router.push(`/shop/product/${id}`)
}

function onPageChange(page: number) {
  currentPage.value = page
  loadProducts()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => { loadProducts() })
</script>

<style scoped>
.product-feed { max-width: 1400px; margin: 0 auto; padding: 0 24px 40px; }

/* Hero Filter Area */
.hero-filter {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  margin: 24px 0 32px;
  padding: 40px 48px;
}
.hero-content { max-width: 800px; margin: 0 auto; text-align: center; }
.hero-title { font-size: 28px; font-weight: 700; color: #fff; margin: 0 0 24px; }
.hero-search { margin-bottom: 20px; }
.hero-search :deep(.el-input__wrapper) {
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}
.hero-styles {
  display: flex; justify-content: center;
}
.hero-styles :deep(.el-radio-button__inner) {
  background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.2); color: rgba(255,255,255,0.9);
}
.hero-styles :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #fff; color: #667eea; border-color: #fff;
}

/* Product Grid */
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}
.product-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}
.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.12);
}
.card-image {
  position: relative;
  height: 200px;
  overflow: hidden;
  background: #f5f7fa;
}
.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.style-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,0.6);
  color: white;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 12px;
}
.card-body { padding: 16px; display: flex; flex-direction: column; min-height: 235px; }
.card-title {
  font-size: 17px; line-height: 1.45; margin: 0 0 7px; color: #303133;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.card-subtitle {
  color: #606266; font-size: 14px; line-height: 1.5; margin: 0 0 8px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.card-summary {
  color: #909399; font-size: 13px; line-height: 1.55; margin: 0 0 10px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.card-highlights { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.card-highlights span { font-size: 11px; color: #8a5a00; background: #fff7e6; padding: 3px 7px; border-radius: 6px; }
.card-meta { display: flex; gap: 10px; color: #a0a3aa; font-size: 12px; margin-top: auto; }
.card-category { color: #667eea; }
.card-store { font-size: 12px; color: #ff6b35; margin: 8px 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-footer { display: flex; justify-content: space-between; align-items: center; }
.card-price { font-size: 20px; font-weight: bold; color: #e74c3c; }
.view-detail { font-size: 12px; color: #667eea; }
.pagination { display: flex; justify-content: center; margin-top: 32px; }
.loading-state { padding: 40px; }
</style>
