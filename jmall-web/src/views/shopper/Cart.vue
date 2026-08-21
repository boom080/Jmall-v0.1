<template>
  <div class="cart-page">
    <h2>🛒 购物车</h2>

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

    <div v-else class="cart-content">
      <div class="cart-list">
        <div v-for="item in items" :key="item.id" class="cart-item">
          <img :src="parseImage(item.images)" :alt="item.title" class="cart-item-img" />
          <div class="cart-item-info">
            <h4>{{ item.title }}</h4>
            <span class="cart-item-price">¥{{ formatPrice(item.price) }}</span>
            <el-tag v-if="item.purchasable === false" type="warning" size="small" class="unavailable-tag">
              {{ item.unavailableReason || '暂不可购买' }}
            </el-tag>
          </div>
          <div class="cart-item-qty">
            <el-input-number
              v-model="item.quantity"
              :min="1"
              :max="99"
              size="small"
              @change="(v: number) => updateQty(item, v)"
            />
          </div>
          <span class="cart-item-subtotal">¥{{ formatPrice(item.price * item.quantity) }}</span>
          <el-button type="danger" size="small" circle @click="removeItem(item)">
            <el-icon><Delete /></el-icon>
          </el-button>
        </div>
      </div>

      <div class="cart-footer">
        <div class="cart-total">
          合计：<span class="total-price">¥{{ formatPrice(totalAmount) }}</span>
        </div>
        <div class="cart-actions">
          <el-button @click="clearAll">清空购物车</el-button>
          <el-button type="primary" size="large" @click="checkout" :loading="checkingOut">
            去结算 ({{ items.length }} 件)
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cartApi } from '@/services/products'
import type { CartItem } from '@/types'

const router = useRouter()
const items = ref<CartItem[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const checkingOut = ref(false)

function formatPrice(p: number) { return (p / 100).toFixed(2) }
function parseImage(images: string): string {
  try {
    const arr = JSON.parse(images)
    return arr[0] || 'https://placehold.co/120x120/e8e8e8/999?text=商品'
  } catch { return 'https://placehold.co/120x120/e8e8e8/999?text=商品' }
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

async function updateQty(item: CartItem, qty: number) {
  try {
    await cartApi.updateQuantity(item.id, qty)
  } catch {
    ElMessage.error('更新数量失败')
  }
}

async function removeItem(item: CartItem) {
  try {
    await cartApi.remove(item.id)
    items.value = items.value.filter(i => i.id !== item.id)
    ElMessage.success('已移除')
  } catch {
    ElMessage.error('移除失败')
  }
}

async function clearAll() {
  try {
    await ElMessageBox.confirm('确定清空购物车？', '提示', { type: 'warning' })
    await cartApi.clear()
    items.value = []
    ElMessage.success('购物车已清空')
  } catch { /* cancelled */ }
}

async function checkout() {
  if (unavailableItems.value.length > 0) {
    ElMessage.warning('请先移除不可结算的商品')
    return
  }
  checkingOut.value = true
  try {
    router.push('/shop/checkout')
  } finally {
    checkingOut.value = false
  }
}

onMounted(() => loadCart())
</script>

<style scoped>
.cart-page { padding: 40px; max-width: 900px; margin: 0 auto; }
.cart-content { margin-top: 24px; }
.cart-item {
  display: flex; align-items: center; gap: 16px;
  padding: 16px; margin-bottom: 12px;
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.cart-item-img { width: 80px; height: 80px; object-fit: cover; border-radius: 8px; }
.cart-item-info { flex: 1; }
.cart-item-info h4 { margin: 0 0 4px; font-size: 15px; }
.cart-item-price { color: #999; font-size: 13px; }
.unavailable-tag { display: block; width: fit-content; margin-top: 6px; }
.cart-item-subtotal { font-weight: bold; color: #e74c3c; min-width: 80px; text-align: right; }
.cart-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px; margin-top: 16px;
  background: white; border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.cart-total { font-size: 16px; }
.total-price { font-size: 24px; font-weight: bold; color: #e74c3c; }
.cart-actions { display: flex; gap: 12px; }
.state-container { padding: 40px; }
</style>
