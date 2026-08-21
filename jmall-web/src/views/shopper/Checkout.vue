<template>
  <div class="checkout-page">
    <h2>💳 结算</h2>

    <div v-if="loading" class="state-container">
      <el-skeleton :rows="4" animated />
    </div>

    <el-result
      v-else-if="error"
      icon="error" title="加载失败" :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadCart">🔄 重新加载</el-button>
      </template>
    </el-result>

    <el-empty v-else-if="items.length === 0" description="购物车是空的">
      <el-button type="primary" @click="$router.push('/shop')">🛒 去逛逛</el-button>
    </el-empty>

    <div v-else class="checkout-content">
      <el-alert
        v-if="unavailableItems.length"
        title="购物车含不可结算商品，请返回购物车移除后再支付"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      />
      <el-card shadow="never" class="summary-card">
        <template #header>📋 订单摘要</template>
        <div class="summary-list">
          <div v-for="item in items" :key="item.id" class="summary-item">
            <img :src="parseImage(item.images)" :alt="item.title" />
            <div class="summary-info">
              <span class="summary-title">{{ item.title }}</span>
              <span class="summary-qty">×{{ item.quantity }}</span>
              <el-tag v-if="item.purchasable === false" type="warning" size="small">
                {{ item.unavailableReason || '暂不可购买' }}
              </el-tag>
            </div>
            <span class="summary-price">¥{{ formatPrice(item.price * item.quantity) }}</span>
          </div>
        </div>
        <el-divider />
        <div class="summary-total">
          应付总额：<span class="total-price">¥{{ formatPrice(totalAmount) }}</span>
        </div>
      </el-card>

      <div class="checkout-actions">
        <el-button @click="$router.back()">返回购物车</el-button>
        <el-button type="success" size="large" @click="pay" :loading="paying" :disabled="unavailableItems.length > 0">
          💰 确认支付 ¥{{ formatPrice(totalAmount) }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { cartApi, orderApi } from '@/services/products'
import type { CartItem } from '@/types'

const router = useRouter()
const items = ref<CartItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const paying = ref(false)

function formatPrice(p: number) { return (p / 100).toFixed(2) }
function parseImage(images: string): string {
  try {
    const arr = JSON.parse(images)
    return arr[0] || 'https://placehold.co/80x80/e8e8e8/999?text=商品'
  } catch { return 'https://placehold.co/80x80/e8e8e8/999?text=商品' }
}

const totalAmount = computed(() => items.value.reduce((s, i) => s + i.price * i.quantity, 0))
const unavailableItems = computed(() => items.value.filter(i => i.purchasable === false))

async function loadCart() {
  loading.value = true
  error.value = null
  try {
    items.value = await cartApi.list()
  } catch (e: any) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function pay() {
  if (unavailableItems.value.length > 0) {
    ElMessage.warning('请先返回购物车移除不可结算商品')
    return
  }
  paying.value = true
  try {
    const result = await orderApi.checkout()
    ElMessage.success(`支付成功！共 ${result.totalOrders} 件商品`)
    router.push('/shop/orders')
  } catch (e: any) {
    ElMessage.error(e.message || '支付失败')
  } finally {
    paying.value = false
  }
}

onMounted(() => loadCart())
</script>

<style scoped>
.checkout-page { padding: 40px; max-width: 700px; margin: 0 auto; }
.checkout-content { margin-top: 24px; }
.summary-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}
.summary-item img { width: 60px; height: 60px; object-fit: cover; border-radius: 8px; }
.summary-info { flex: 1; }
.summary-title { font-size: 14px; }
.summary-qty { font-size: 12px; color: #999; margin-left: 8px; }
.summary-price { font-weight: bold; color: #e74c3c; }
.summary-total { text-align: right; font-size: 16px; margin-top: 8px; }
.total-price { font-size: 28px; font-weight: bold; color: #e74c3c; }
.checkout-actions { display: flex; justify-content: space-between; margin-top: 24px; }
.state-container { padding: 40px; }
</style>
