<template>
  <section class="home-view">
    <div class="hero">
      <div>
        <p class="eyebrow">Jrunmall User</p>
        <h1>面向用户端重建的现代商城前台</h1>
        <p>
          当前首页、商品列表、商品详情、购物车、订单和模拟支付都优先对接 Java 正式业务接口；只有在文档明确允许的场景下才回退到占位展示。
        </p>
        <div class="hero__actions">
          <RouterLink to="/products" class="primary-link">进入商品列表</RouterLink>
          <RouterLink to="/cart" class="secondary-link">查看购物车</RouterLink>
        </div>
      </div>
      <img src="/placeholders/products/default-product.svg" alt="商品占位图" class="hero__image" />
    </div>

    <header class="section-header">
      <div>
        <p class="eyebrow">精选推荐</p>
        <h2>首页推荐商品</h2>
        <p>优先展示真实接口返回的商品卡片，支持直接加入购物车。</p>
      </div>
      <span class="data-source">
        {{ featured.source === 'api' ? '真实接口' : '本地 fallback' }}
      </span>
    </header>

    <p v-if="featured.errorMessage" class="inline-error">{{ featured.errorMessage }}</p>
    <p v-if="feedbackMessage" class="inline-success">{{ feedbackMessage }}</p>
    <div v-if="cartConfirmation" class="cart-confirmation" role="status">
      <span>{{ cartConfirmation.title }} 已加入购物车，当前购物车共 {{ cartConfirmation.totalCount }} 件商品。</span>
      <RouterLink to="/cart" class="secondary-link">去购物车确认</RouterLink>
    </div>

    <div v-if="featured.items.length" class="product-grid">
      <ProductCard v-for="product in featured.items" :key="product.id" :product="product" @add-to-cart="handleAddToCart" />
    </div>
    <section v-else class="empty-block">
      <h2>暂无推荐商品</h2>
      <p>当前未查询到可展示的商品数据。</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import ProductCard from '@/components/ProductCard.vue'
import { fetchFeaturedProducts } from '@/services/catalog'
import { addCartItem } from '@/services/commerce'
import { useAuthStore } from '@/store/auth'
import { useUserUiStore } from '@/store/ui'
import type { ProductListResult } from '@/types/product'

const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUserUiStore()
const featured = reactive<ProductListResult>({
  source: 'fallback',
  items: [],
})
const feedbackMessage = ref('')
const cartConfirmation = ref<{ title: string; totalCount: number } | null>(null)
let confirmationTimer: number | undefined

onMounted(async () => {
  const result = await fetchFeaturedProducts(4)
  featured.source = result.source
  featured.items = result.items
  featured.errorMessage = result.errorMessage
})

async function handleAddToCart(productId: number) {
  feedbackMessage.value = ''
  cartConfirmation.value = null
  if (!authStore.isAuthenticated) {
    await router.push({ name: 'login', query: { redirect: '/' } })
    return
  }
  try {
    const cart = await addCartItem(productId, 1)
    uiStore.setCartCount(cart.totalCount)
    const product = featured.items.find((item) => item.id === productId)
    cartConfirmation.value = {
      title: product?.title || '商品',
      totalCount: cart.totalCount,
    }
    feedbackMessage.value = '已加入购物车，可继续浏览或直接结算。'
    resetConfirmationTimer()
  } catch (error) {
    if (error instanceof Error && error.message.includes('请先登录')) {
      authStore.clear()
      await router.push({ name: 'login', query: { redirect: '/' } })
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


