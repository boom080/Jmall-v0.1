<template>
  <div class="collection-page">
    <h2>🏠 我的拥有</h2>
    <p class="subtitle">已收藏 {{ collections.length }} 件宝贝</p>

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
        <el-button type="primary" @click="loadCollections">🔄 重新加载</el-button>
      </template>
    </el-result>

    <!-- Empty State -->
    <div v-else-if="collections.length === 0" class="empty-state">
      <el-empty description="还没有收藏商品">
        <el-button type="primary" @click="$router.push('/shop')">🛒 去逛逛</el-button>
      </el-empty>
    </div>

    <div v-else class="collection-grid">
      <div v-for="item in collections" :key="item.id" class="collection-card">
        <img :src="getImage(item)" :alt="item.title" />
        <div class="card-info">
          <h4>{{ item.title }}</h4>
          <span class="price">¥{{ formatPrice(item.price || 0) }}</span>
          <span class="date">{{ formatDate(item.createdAt) }}</span>
          <el-button size="small" type="danger" plain @click="uncollect(item)" :loading="uncollectingId === (item.id || item.productId)">
            💔 取消收藏
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import http from '@/services/http'
import { ElMessage } from 'element-plus'

const collections = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const uncollectingId = ref<number | null>(null)

function formatPrice(p: number) { return (p / 100).toFixed(2) }
function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }
function getImage(item: any): string {
  try {
    const imgs = typeof item.images === 'string' ? JSON.parse(item.images) : item.images
    if (Array.isArray(imgs) && imgs.length > 0) return imgs[0]
  } catch {}
  return 'https://placehold.co/300x300/e8e8e8/999?text=📦'
}

onMounted(() => { loadCollections() })

async function loadCollections() {
  loading.value = true
  error.value = null
  try {
    collections.value = await http.get('/collections')
  } catch (e: any) {
    error.value = e.message || '加载收藏列表失败'
    collections.value = []
  } finally {
    loading.value = false
  }
}

async function uncollect(item: any) {
  const pid = item.id || item.productId
  uncollectingId.value = pid
  try {
    await http.delete(`/collections/${pid}`)
    collections.value = collections.value.filter(c => (c.id || c.productId) !== pid)
    ElMessage.success('已取消收藏')
  } catch (e: any) {
    ElMessage.error(e.message || '取消收藏失败')
  } finally {
    uncollectingId.value = null
  }
}
</script>

<style scoped>
.collection-page { padding: 40px; max-width: 1200px; margin: 0 auto; }
.subtitle { color: #999; margin-bottom: 24px; }
.collection-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 20px; }
.collection-card { background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.collection-card img { width: 100%; height: 200px; object-fit: cover; }
.card-info { padding: 16px; }
.card-info h4 { margin: 0 0 8px; font-size: 15px; }
.price { font-weight: bold; color: #e74c3c; display: block; }
.date { display: block; font-size: 12px; color: #999; margin: 4px 0 8px; }
.empty-state { padding: 80px 0; }
.loading-state { padding: 40px 0; }
</style>
