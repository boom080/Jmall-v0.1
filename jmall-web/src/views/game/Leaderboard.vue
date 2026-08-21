<template>
  <div class="leaderboard-page">
    <h2>📊 畅销榜</h2>
    <p class="subtitle">基于真实销量数据 · 实时更新</p>

    <el-tabs v-model="activeTab" @tab-change="loadData">
      <el-tab-pane label="🏆 畅销商品" name="products" />
      <el-tab-pane label="🏪 畅销商家" name="sellers" />
    </el-tabs>

    <el-tabs v-if="activeTab === 'products'" v-model="period" @tab-change="loadData" class="period-tabs">
      <el-tab-pane label="📅 本周" name="week" />
      <el-tab-pane label="📅 本月" name="month" />
      <el-tab-pane label="👑 历史总榜" name="all" />
    </el-tabs>

    <el-tabs v-if="activeTab === 'sellers'" v-model="period" @tab-change="loadData" class="period-tabs">
      <el-tab-pane label="📅 本周" name="week" />
      <el-tab-pane label="📅 本月" name="month" />
      <el-tab-pane label="👑 历史总榜" name="all" />
    </el-tabs>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- Error State -->
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadData">🔄 重新加载</el-button>
      </template>
    </el-result>

    <!-- Empty State -->
    <el-empty v-else-if="productEntries.length === 0 && sellerEntries.length === 0" description="暂无排行数据" />

    <!-- Product Ranking -->
    <div v-else-if="activeTab === 'products' && productEntries.length > 0" class="leaderboard-list">
      <div
        v-for="(entry, index) in productEntries"
        :key="entry.id"
        class="leaderboard-item clickable"
        :class="`rank-${index + 1}`"
        @click="$router.push(`/shop/product/${entry.id}`)"
      >
        <span class="rank-badge">{{ index + 1 <= 3 ? ['🥇','🥈','🥉'][index] : `#${index + 1}` }}</span>
        <img :src="parseImage(entry.images)" class="product-thumb" />
        <div class="product-info">
          <span class="product-name">{{ entry.title }}</span>
          <span class="product-meta">{{ entry.category }} · ¥{{ formatPrice(entry.price) }}</span>
          <span v-if="entry.storeId" class="product-store" @click.stop="$router.push(`/store/${entry.storeId}`)">🏪 {{ entry.storeName }} →</span>
        </div>
        <span class="sales-count">📦 已售 {{ formatNumber(entry.saleCount) }}</span>
      </div>
    </div>

    <!-- Seller Ranking -->
    <div v-else-if="activeTab === 'sellers' && sellerEntries.length > 0" class="leaderboard-list">
      <div
        v-for="(entry, index) in sellerEntries"
        :key="entry.userId"
        class="leaderboard-item clickable"
        :class="`rank-${index + 1}`"
        @click="entry.storeId ? $router.push(`/store/${entry.storeId}`) : null"
      >
        <span class="rank-badge">{{ index + 1 <= 3 ? ['🥇','🥈','🥉'][index] : `#${index + 1}` }}</span>
        <div class="seller-info">
          <span class="seller-name">🏪 {{ entry.storeName || entry.username }} {{ entry.storeId ? '→' : '' }}</span>
          <span v-if="entry.ownerName" class="seller-owner">店主：{{ entry.ownerName }}</span>
        </div>
        <span class="sales-count">📦 累计 {{ formatNumber(entry.totalSales || entry.totalSpent) }} 件</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { gamificationApi } from '@/services/gamification'

const activeTab = ref('products')
const period = ref('all')
const loading = ref(true)
const error = ref<string | null>(null)
const productEntries = ref<any[]>([])
const sellerEntries = ref<any[]>([])

function formatPrice(p: number) { return (p / 100).toFixed(2) }
function formatNumber(n: number) {
  if (n >= 1e8) return (n/1e8).toFixed(1)+'亿'
  if (n >= 1e4) return (n/1e4).toFixed(1)+'万'
  return n.toLocaleString()
}
function parseImage(images: string): string {
  try {
    const arr = JSON.parse(images)
    return arr[0] || 'https://placehold.co/60x60/e8e8e8/999?text=商品'
  } catch { return 'https://placehold.co/60x60/e8e8e8/999?text=商品' }
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    if (activeTab.value === 'products') {
      productEntries.value = await gamificationApi.getTopProducts(period.value as any)
    } else {
      sellerEntries.value = await gamificationApi.getTopSellers(period.value as any)
    }
  } catch (e: any) {
    error.value = e.message || '加载排行榜失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => loadData())
</script>

<style scoped>
.leaderboard-page { padding: 40px; max-width: 750px; margin: 0 auto; }
.subtitle { color: #999; margin-bottom: 24px; }
.period-tabs { margin-bottom: 16px; }
.leaderboard-item {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px; margin-bottom: 8px;
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: transform 0.2s;
}
.leaderboard-item:hover { transform: translateX(4px); }
.leaderboard-item.clickable { cursor: pointer; }
.rank-badge { font-size: 24px; min-width: 42px; text-align: center; }
.product-thumb { width: 48px; height: 48px; object-fit: cover; border-radius: 8px; }
.product-info { flex: 1; display: flex; flex-direction: column; }
.product-name { font-weight: 500; font-size: 15px; }
.product-meta { font-size: 12px; color: #999; }
.product-store { font-size: 12px; color: #667eea; cursor: pointer; }
.product-store:hover { text-decoration: underline; }
.product-store { font-size: 12px; color: #ff6b35; }
.seller-info { flex: 1; display: flex; flex-direction: column; }
.seller-name { font-weight: 500; font-size: 16px; }
.seller-owner { font-size: 12px; color: #999; }
.sales-count { font-weight: bold; color: #e74c3c; font-size: 15px; white-space: nowrap; }
.rank-1 { border-left: 4px solid #ffd700; }
.rank-2 { border-left: 4px solid #c0c0c0; }
.rank-3 { border-left: 4px solid #cd7f32; }
.loading-state { padding: 40px 0; }
</style>
