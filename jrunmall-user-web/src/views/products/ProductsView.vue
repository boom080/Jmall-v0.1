<template>
  <section class="products-view">
    <header class="section-header">
      <div>
        <p class="eyebrow">商品列表</p>
        <h2>用户端商品展示</h2>
        <p>当前优先展示商品封面、标题、分类、卖点和价格，并支持直接加入购物车。</p>
      </div>
      <span class="data-source">
        {{ catalog.source === 'api' ? '真实接口' : '本地 fallback' }}
      </span>
    </header>

    <p v-if="catalog.errorMessage" class="inline-error">{{ catalog.errorMessage }}</p>
    <p v-if="feedbackMessage" class="inline-success">{{ feedbackMessage }}</p>
    <div v-if="cartConfirmation" class="cart-confirmation" role="status">
      <span>{{ cartConfirmation.title }} 已加入购物车，当前购物车共 {{ cartConfirmation.totalCount }} 件商品。</span>
      <RouterLink to="/cart" class="secondary-link">去购物车确认</RouterLink>
    </div>

    <div v-if="catalog.items.length" class="product-grid">
      <ProductCard v-for="product in catalog.items" :key="product.id" :product="product" @add-to-cart="handleAddToCart" />
    </div>
    <section v-else class="empty-block">
      <h2>暂无可展示商品</h2>
      <p>当前商品接口已返回空结果。</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import ProductCard from '@/components/ProductCard.vue'
import { fetchCatalogProducts } from '@/services/catalog'
import { addCartItem } from '@/services/commerce'
import { useAuthStore } from '@/store/auth'
import { useUserUiStore } from '@/store/ui'
import type { ProductListResult } from '@/types/product'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUserUiStore()
const catalog = reactive<ProductListResult>({
  source: 'fallback',
  items: [],
})
const feedbackMessage = ref('')
const cartConfirmation = ref<{ title: string; totalCount: number } | null>(null)
let confirmationTimer: number | undefined

onMounted(async () => {
  const result = await fetchCatalogProducts()
  catalog.source = result.source
  catalog.items = result.items
  catalog.errorMessage = result.errorMessage
})

async function handleAddToCart(productId: number) {
  feedbackMessage.value = ''
  cartConfirmation.value = null
  if (!authStore.isAuthenticated) {
    await router.push({ name: 'login', query: { redirect: '/products' } })
    return
  }
  try {
    const cart = await addCartItem(productId, 1)
    uiStore.setCartCount(cart.totalCount)
    const product = catalog.items.find((item) => item.id === productId)
    cartConfirmation.value = {
      title: product?.title || '商品',
      totalCount: cart.totalCount,
    }
    feedbackMessage.value = '已加入购物车，可前往购物车继续下单。'
    resetConfirmationTimer()
  } catch (error) {
    if (error instanceof Error && error.message.includes('请先登录')) {
      authStore.clear()
      await router.push({ name: 'login', query: { redirect: '/products' } })
      return
    }
    feedbackMessage.value = error instanceof Error ? error.message : '加入购物车失败'
  }
}

function resetConfirmationTimer() {
  if (confirmationTimer) {
    window.clearTimeout(confirmationTimer)
  }
  confirmationTimer = window.setTimeout(() => {
    cartConfirmation.value = null
  }, 5000)
}

onUnmounted(() => {
  if (confirmationTimer) {
    window.clearTimeout(confirmationTimer)
  }
})
</script>


