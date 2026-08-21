<template>
  <!-- Loading State -->
  <div v-if="loading" class="state-container">
    <el-skeleton :rows="6" animated />
  </div>

  <!-- Error State -->
  <el-result
    v-else-if="error"
    icon="error"
    title="加载失败"
    :sub-title="error"
  >
    <template #extra>
      <el-button type="primary" @click="loadProduct">🔄 重新加载</el-button>
    </template>
  </el-result>

  <!-- Not Found -->
  <el-result
    v-else-if="!product"
    icon="warning"
    title="商品不存在"
    sub-title="该商品可能已下架或不存在"
  >
    <template #extra>
      <el-button type="primary" @click="$router.push('/shop')">🛒 浏览其他商品</el-button>
    </template>
  </el-result>

  <!-- Product Detail -->
  <div class="product-detail" v-else>
    <div class="detail-main">
      <div class="detail-image">
        <img :src="getProductImage(product.images, product.category)" :alt="product.title" />
      </div>
      <div class="detail-info">
        <span class="style-badge">{{ styleLabel(product.style) }}</span>
        <h1>{{ product.title }}</h1>
        <p v-if="product.subtitle" class="subtitle">{{ product.subtitle }}</p>
        <p class="category">{{ product.category }}</p>
        <div class="price-section">
          <span class="price">🪙 {{ formatPrice(product.price) }}</span>
        </div>
        <div class="stats">
          <span>👁️ {{ formatViews(product.viewCount) }} 次浏览</span>
          <span>❤️ {{ formatViews(product.likeCount) }} 点赞</span>
          <span>📦 {{ formatViews(product.saleCount) }} 已售</span>
        </div>
        <div v-if="sellingPoints.length" class="selling-points">
          <span v-for="point in sellingPoints" :key="point">✓ {{ point }}</span>
        </div>
        <p v-if="product.storeName && product.storeId" class="store-name" @click="$router.push(`/store/${product.storeId}`)">🏪 {{ product.storeName }} →</p>
        <div class="actions">
          <el-button type="primary" size="large" @click="addToCart" :loading="addingToCart" :disabled="isOwnProduct">
            {{ isOwnProduct ? '这是你自己的商品' : '🛒 加入购物车' }}
          </el-button>
          <el-button size="large" @click="toggleCollect" :type="collected ? 'danger' : 'default'">
            {{ collected ? '❤️ 已收藏' : '🤍 收藏' }}
          </el-button>
        </div>
      </div>
    </div>
    <section class="detail-content">
      <h2>商品详情</h2>
      <div class="description">{{ product.description || product.aiDetail || '商家暂未填写详细说明' }}</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { productApi, cartApi } from '@/services/products'
import http from '@/services/http'
import { getProductImage } from '@/services/imageUtils'
import { ElMessage } from 'element-plus'
import type { Product } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const product = ref<Product | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const addingToCart = ref(false)
const collected = ref(false)
const sellingPoints = computed(() => {
  const raw = product.value?.aiSellingPoints
  if (Array.isArray(raw)) return raw.map(String).filter(Boolean).slice(0, 5)
  if (typeof raw !== 'string' || !raw.trim()) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.map(String).filter(Boolean).slice(0, 5) : []
  } catch { return [] }
})
const isOwnProduct = computed(() => Boolean(
  (authStore.currentUser?.storeId && product.value?.storeId === authStore.currentUser.storeId)
  || (product.value?.purchasable === false
      && product.value?.unavailableReason?.includes('自己店铺'))
))

function formatPrice(p: number) { return (p / 100).toFixed(2) }
function formatViews(n: number) {
  const count = n || 0
  return count >= 10000 ? (count/10000).toFixed(1)+'万' : count.toLocaleString()
}
function styleLabel(s: string) {
  const labels: Record<string,string> = { pinduoduo:'拼多多风', taobao:'淘宝风', jd:'京东风', suning:'苏宁风', xiaohongshu:'小红书风' }
  return labels[s] || ''
}

async function addToCart() {
  if (!authStore.isAuthenticated) { router.push('/login'); return }
  if (isOwnProduct.value) { ElMessage.warning('不能购买自己店铺的商品'); return }
  addingToCart.value = true
  try {
    await cartApi.add(product.value!.id, 1)
    ElMessage.success('已加入购物车')
  } catch (e: any) { ElMessage.error(e.message || '加入购物车失败') }
  finally { addingToCart.value = false }
}

async function toggleCollect() {
  if (!authStore.isAuthenticated) { router.push('/login'); return }
  try {
    if (collected.value) {
      await http.delete(`/collections/${product.value!.id}`)
      collected.value = false
      ElMessage.success('已取消收藏')
    } else {
      await http.post(`/collections/${product.value!.id}`)
      collected.value = true
      ElMessage.success('已加入收藏')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

onMounted(() => { loadProduct() })

async function loadProduct() {
  loading.value = true
  error.value = null
  try {
    product.value = await productApi.get(Number(route.params.id))
    // Check if already collected (only for authenticated users)
    if (authStore.isAuthenticated) {
      try {
        collected.value = await http.get(`/collections/check/${product.value!.id}`)
      } catch { /* ignore */ }
    }
  } catch (e: any) {
    error.value = e.message || '加载商品信息失败'
    product.value = null
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.product-detail { max-width: 1100px; margin: 40px auto; padding: 0 24px; }
.detail-main { display: flex; gap: 40px; background: white; border-radius: 20px; padding: 40px; }
.detail-image { flex: 1; }
.detail-image img { width: 100%; border-radius: 12px; }
.detail-info { flex: 1; }
.style-badge { background: var(--primary-light); color: white; padding: 2px 12px; border-radius: 12px; font-size: 13px; }
.detail-info h1 { font-size: 28px; margin: 12px 0 8px; }
.subtitle { margin: 0 0 8px; color: #606266; font-size: 17px; line-height: 1.6; }
.category { color: #999; }
.price-section { margin: 20px 0; }
.price { font-size: 36px; font-weight: bold; color: #e74c3c; }
.stats { display: flex; gap: 20px; font-size: 14px; color: #666; margin-bottom: 20px; }
.selling-points { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
.selling-points span { background: #f0f5ff; color: #5166ad; border-radius: 8px; padding: 6px 10px; font-size: 13px; }
.detail-content { background: #fff; margin-top: 24px; padding: 36px 44px; border-radius: 20px; }
.detail-content h2 { margin: 0 0 22px; font-size: 24px; }
.description { white-space: pre-line; font-size: 16px; line-height: 2; color: #4a4d55; margin: 0; }
.actions { display: flex; gap: 12px; }
.loading { padding: 40px; }
.state-container { padding: 80px 0; display: flex; justify-content: center; max-width: 600px; margin: 0 auto; }
</style>
