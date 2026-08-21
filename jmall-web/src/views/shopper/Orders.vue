<template>
  <div class="orders-page">
    <h2>📦 我的订单</h2>

    <div v-if="loading" class="state-container">
      <el-skeleton :rows="3" animated />
    </div>

    <el-result
      v-else-if="error"
      icon="error" title="加载失败" :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadOrders">🔄 重新加载</el-button>
      </template>
    </el-result>

    <el-empty v-else-if="orders.length === 0" description="还没有订单">
      <el-button type="primary" @click="$router.push('/shop')">🛒 去逛逛</el-button>
    </el-empty>

    <div v-else class="order-list">
      <div v-for="order in orders" :key="order.id" class="order-item">
        <img :src="parseImage(order.productImage)" :alt="order.productTitle" class="order-img" />
        <div class="order-info">
          <h4>{{ order.productTitle }}</h4>
          <span class="order-qty">×{{ order.quantity }}</span>
          <el-tag size="small" :type="statusTag(order.status)">{{ statusLabel(order.status) }}</el-tag>
        </div>
        <div class="order-right">
          <span class="order-price">¥{{ formatPrice(order.amount) }}</span>
          <span class="order-date">{{ formatDate(order.createdAt) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { orderApi } from '@/services/products'
import type { Order } from '@/types'

const orders = ref<Order[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

function formatPrice(p: number) { return (p / 100).toFixed(2) }
function formatDate(d: string) { return new Date(d).toLocaleDateString('zh-CN') }
function parseImage(images: string): string {
  try {
    const arr = JSON.parse(images)
    return arr[0] || 'https://placehold.co/80x80/e8e8e8/999?text=订单'
  } catch { return 'https://placehold.co/80x80/e8e8e8/999?text=订单' }
}
function statusTag(s: string) { return s === 'paid' ? 'success' : s === 'cancelled' ? 'danger' : 'warning' }
function statusLabel(s: string) {
  const labels: Record<string, string> = { paid: '已支付', shipped: '已发货', completed: '已完成', cancelled: '已取消' }
  return labels[s] || s
}

async function loadOrders() {
  loading.value = true
  error.value = null
  try {
    orders.value = await orderApi.list()
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => loadOrders())
</script>

<style scoped>
.orders-page { padding: 40px; max-width: 800px; margin: 0 auto; }
.order-list { margin-top: 24px; }
.order-item {
  display: flex; align-items: center; gap: 16px;
  padding: 16px; margin-bottom: 12px;
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.order-img { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
.order-info { flex: 1; }
.order-info h4 { margin: 0 0 4px; font-size: 15px; }
.order-qty { font-size: 13px; color: #999; margin-right: 8px; }
.order-right { text-align: right; }
.order-price { font-size: 18px; font-weight: bold; color: #e74c3c; display: block; }
.order-date { font-size: 12px; color: #999; }
.state-container { padding: 40px; }
</style>
