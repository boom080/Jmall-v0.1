<template>
  <section class="commerce-panel">
    <header class="section-header">
      <div>
        <p class="eyebrow">购物车</p>
        <h2>准备下单的商品</h2>
        <p>购物车数据由 Redis 承载，当前已经切到真实登录用户上下文。</p>
      </div>
      <span class="data-source">{{ cart.source === 'api' ? 'Redis 购物车' : '本地空态' }}</span>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="inline-success">{{ successMessage }}</p>

    <section v-if="cart.items.length" class="commerce-grid">
      <article class="commerce-card">
        <div v-for="item in cart.items" :key="item.skuId" class="cart-item">
          <img :src="item.coverUrl" :alt="item.title" class="cart-item__image" />
          <div class="cart-item__body">
            <h3>{{ item.title }}</h3>
            <p>{{ item.category }}</p>
            <p>{{ item.summary }}</p>
            <div class="cart-item__controls">
              <button type="button" class="secondary-link button-reset" @click="changeQuantity(item.skuId, item.quantity - 1)">-</button>
              <span>{{ item.quantity }}</span>
              <button type="button" class="secondary-link button-reset" @click="changeQuantity(item.skuId, item.quantity + 1)">+</button>
              <button type="button" class="link-button" @click="removeItem(item.skuId)">删除</button>
            </div>
          </div>
          <strong>￥{{ item.totalAmount }}</strong>
        </div>
      </article>

      <aside class="commerce-card commerce-card--summary">
        <dl class="summary-list">
          <div>
            <dt>当前用户</dt>
            <dd>{{ cart.displayName }}</dd>
          </div>
          <div>
            <dt>商品件数</dt>
            <dd>{{ cart.totalCount }}</dd>
          </div>
          <div>
            <dt>合计金额</dt>
            <dd>￥{{ cart.totalAmount }}</dd>
          </div>
        </dl>
        <div class="hero__actions">
          <RouterLink to="/checkout" class="primary-link">去下单</RouterLink>
          <RouterLink to="/products" class="secondary-link">继续逛商品</RouterLink>
        </div>
      </aside>
    </section>

    <section v-else class="empty-block">
      <h2>购物车还是空的</h2>
      <p>先去商品列表挑选商品，再回来完成模拟下单与支付。</p>
      <RouterLink to="/products" class="primary-link">去逛商品</RouterLink>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import { fetchCartItems, removeCartItem, updateCartItem } from '@/services/commerce'
import { useUserUiStore } from '@/store/ui'
import type { CartSnapshot } from '@/types/commerce'

const uiStore = useUserUiStore()
const cart = reactive<CartSnapshot>({
  source: 'fallback',
  userId: 0,
  displayName: '',
  totalCount: 0,
  totalAmount: 0,
  items: [],
})
const errorMessage = ref('')
const successMessage = ref('')

onMounted(loadCart)

async function loadCart() {
  const result = await fetchCartItems()
  hydrate(result)
}

async function changeQuantity(skuId: number, nextQuantity: number) {
  successMessage.value = ''
  errorMessage.value = ''
  if (nextQuantity <= 0) {
    await removeItem(skuId)
    return
  }
  try {
    const snapshot = await updateCartItem(skuId, nextQuantity)
    hydrate(snapshot)
    successMessage.value = '购物车数量已更新'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '更新数量失败'
  }
}

async function removeItem(skuId: number) {
  successMessage.value = ''
  errorMessage.value = ''
  try {
    const snapshot = await removeCartItem(skuId)
    hydrate(snapshot)
    successMessage.value = '商品已从购物车移除'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '删除购物车项失败'
  }
}

function hydrate(snapshot: CartSnapshot) {
  cart.source = snapshot.source
  cart.userId = snapshot.userId
  cart.displayName = snapshot.displayName
  cart.totalCount = snapshot.totalCount
  cart.totalAmount = snapshot.totalAmount
  cart.items = snapshot.items
  cart.errorMessage = snapshot.errorMessage
  errorMessage.value = snapshot.errorMessage || ''
  uiStore.setCartCount(snapshot.totalCount)
}
</script>


