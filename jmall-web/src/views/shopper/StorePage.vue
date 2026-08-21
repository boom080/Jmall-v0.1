<template>
  <div class="store-page">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="6" animated />
    </div>

    <!-- Error -->
    <el-result
      v-else-if="error"
      icon="error"
      title="店铺不存在"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push('/shop')">🛒 去逛逛</el-button>
      </template>
    </el-result>

    <template v-else-if="store">
      <div v-if="isOwnStore" class="store-toolbar">
        <el-button type="primary" plain @click="backToMerchantCenter">
          ← 返回商家中心
        </el-button>
      </div>

      <!-- Store Header -->
      <div class="store-header">
        <div class="store-banner">
          <div class="store-avatar">
            <el-avatar :size="80" icon="Shop" />
          </div>
          <div class="store-info">
            <div class="store-title-row">
              <h1>{{ store.name }}</h1>
            </div>
            <p class="store-category">📂 {{ store.category || '综合' }}</p>
            <p class="store-desc">{{ store.description || '这个商家很懒，什么都没写~' }}</p>
            <div class="store-stats">
              <span>📦 累计售出 <strong>{{ storeStats.totalSales }}</strong> 件</span>
              <span>🛍️ 在售商品 <strong>{{ storeStats.productCount }}</strong> 件</span>
              <span>🧾 有效订单 <strong>{{ storeStats.totalOrders }}</strong> 笔</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Products Grid -->
      <div class="store-products">
        <h3>🛍️ 店铺商品</h3>
        <el-empty v-if="products.length === 0" description="暂无在售商品" />
        <div v-else class="product-grid">
          <div
            v-for="product in products"
            :key="product.id"
            class="product-card"
            @click="$router.push(`/shop/product/${product.id}`)"
          >
            <img :src="getProductImage(product)" :alt="product.title" class="product-img" />
            <div class="product-body">
              <h4 class="product-title">{{ product.title }}</h4>
              <div class="product-price">¥{{ formatPrice(product.price) }}</div>
              <div class="product-meta">
                <span>👁️ {{ formatCount(product.viewCount) }}</span>
                <span>📦 {{ product.saleCount || 0 }} 已售</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/services/http'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const store = ref<any>(null)
const products = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const storeStats = ref({ productCount: 0, totalSales: 0, totalOrders: 0 })
const isOwnStore = computed(() => {
  const user = authStore.currentUser
  if (!user || !store.value) return false
  return Number(user.storeId) === Number(store.value.id) || Number(user.id) === Number(store.value.userId)
})

function backToMerchantCenter() {
  router.push({ name: 'merchant-dashboard' })
}

function formatPrice(p: number) { return ((p || 0) / 100).toFixed(2) }
function formatCount(n: number) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return n.toString()
}

function getProductImage(product: any): string {
  try {
    if (!product.images) return getPlaceholder(product.category)
    // Try JSON array first
    const imgs = typeof product.images === 'string' ? JSON.parse(product.images) : product.images
    if (Array.isArray(imgs) && imgs.length > 0) return imgs[0]
    // Try comma-separated
    const parts = product.images.split(',')
    if (parts.length > 0 && parts[0].startsWith('http')) return parts[0]
  } catch {}
  return getPlaceholder(product.category)
}

function getPlaceholder(category: string): string {
  const map: Record<string, string> = {
    '食品饮料': 'https://placehold.co/300x300/fff3e0/ff9800?text=🍪',
    '生鲜水果': 'https://placehold.co/300x300/e8f5e9/4caf50?text=🍎',
    '服饰鞋包': 'https://placehold.co/300x300/fce4ec/e91e63?text=👗',
    '家居日用': 'https://placehold.co/300x300/fff8e1/fbc02d?text=🏠',
    '数码家电': 'https://placehold.co/300x300/e3f2fd/2196f3?text=📱',
    '美妆护肤': 'https://placehold.co/300x300/f3e5f5/9c27b0?text=💄',
    '运动户外': 'https://placehold.co/300x300/e8eaf6/3f51b5?text=⚽',
    '图书文娱': 'https://placehold.co/300x300/efebe9/795548?text=📚',
  }
  return map[category] || 'https://placehold.co/300x300/e8e8e8/999?text=📦'
}

onMounted(async () => {
  const storeId = route.params.storeId
  if (!storeId) {
    error.value = '缺少店铺ID'
    loading.value = false
    return
  }

  try {
    const [storeData, productData, statsData]: any[] = await Promise.all([
      http.get(`/stores/${storeId}`),
      http.get(`/products`, { params: { storeId, status: 'published', size: 50 } }),
      http.get(`/stores/${storeId}/stats`),
    ])
    store.value = storeData
    products.value = (productData?.records || productData || [])
    storeStats.value = statsData || storeStats.value
  } catch (e: any) {
    error.value = e.message || '加载店铺失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.store-page { max-width: 1200px; margin: 0 auto; padding: 24px; }
.loading-state { padding: 40px; }
.store-toolbar { display: flex; justify-content: flex-start; margin-bottom: 16px; }

.store-banner {
  display: flex; gap: 24px; padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px; color: #fff; margin-bottom: 32px;
}
.store-avatar { flex-shrink: 0; }
.store-info { flex: 1; }
.store-title-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.store-title-row h1 { margin: 0; font-size: 24px; }
.store-category { font-size: 14px; opacity: 0.85; margin: 0 0 8px; }
.store-desc { font-size: 14px; opacity: 0.8; margin: 0 0 12px; line-height: 1.6; }
.store-stats { display: flex; gap: 24px; font-size: 13px; opacity: 0.9; }
.store-stats strong { font-size: 16px; }

.store-products { margin-top: 24px; }
.store-products h3 { margin: 0 0 16px; font-size: 18px; }

.product-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 16px; }
.product-card {
  background: #fff; border-radius: 12px; overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08); cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }
.product-img { width: 100%; height: 180px; object-fit: cover; }
.product-body { padding: 12px; }
.product-title { margin: 0 0 8px; font-size: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.product-price { font-size: 18px; font-weight: 700; color: #e74c3c; margin-bottom: 6px; }
.product-meta { display: flex; gap: 12px; font-size: 12px; color: #999; }
</style>
