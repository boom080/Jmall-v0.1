<template>
  <section v-if="product" class="product-detail-view">
    <div class="product-detail-view__gallery">
      <img :src="activeImage" :alt="product.title" class="product-detail-view__image" />
      <div v-if="product.imageUrls.length > 1" class="product-detail-view__thumbs">
        <button
          v-for="image in product.imageUrls"
          :key="image"
          type="button"
          class="product-detail-view__thumb"
          @click="activeImage = image"
        >
          <img :src="image" :alt="product.title" />
        </button>
      </div>
    </div>
    <div class="product-detail-view__body">
      <p class="eyebrow">{{ product.category }}</p>
      <h1>{{ product.title }}</h1>
      <p class="product-detail-view__subtitle">{{ product.subtitle }}</p>
      <strong class="price">￥{{ product.price }}</strong>
      <p class="product-detail-view__summary">{{ product.summary }}</p>
      <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
      <p v-if="feedbackMessage" class="inline-success">{{ feedbackMessage }}</p>
      <div v-if="cartConfirmation" class="cart-confirmation" role="status">
        <span>{{ cartConfirmation.title }} 已加入购物车，当前购物车共 {{ cartConfirmation.totalCount }} 件商品。</span>
        <RouterLink to="/cart" class="secondary-link">去购物车确认</RouterLink>
      </div>
      <p class="product-detail-view__detail">{{ product.detail }}</p>
      <ul class="product-detail-view__points">
        <li v-for="point in product.sellingPoints" :key="point">{{ point }}</li>
      </ul>
      <ul v-if="product.detailAttributes.length" class="product-detail-view__points">
        <li v-for="point in product.detailAttributes" :key="point">{{ point }}</li>
      </ul>
      <div class="hero__actions">
        <button type="button" class="primary-link button-reset" @click="handleAddToCart">加入购物车</button>
        <RouterLink to="/products" class="secondary-link">返回列表</RouterLink>
      </div>
    </div>
  </section>
  <section v-else class="empty-block">
    <h2>商品不存在</h2>
    <p v-if="errorMessage">{{ errorMessage }}</p>
    <RouterLink to="/products" class="primary-link">返回商品列表</RouterLink>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchCatalogProductById } from '@/services/catalog'
import { addCartItem } from '@/services/commerce'
import { useAuthStore } from '@/store/auth'
import { useUserUiStore } from '@/store/ui'
import type { CatalogProduct } from '@/types/product'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUserUiStore()
const product = ref<CatalogProduct | null>(null)
const activeImage = ref('/placeholders/products/default-product.svg')
const errorMessage = ref('')
const feedbackMessage = ref('')
const cartConfirmation = ref<{ title: string; totalCount: number } | null>(null)
let confirmationTimer: number | undefined

onMounted(async () => {
  const result = await fetchCatalogProductById(String(route.params.productId))
  product.value = result.product
  activeImage.value = result.product?.coverUrl || '/placeholders/products/default-product.svg'
  errorMessage.value = result.errorMessage || ''
})

async function handleAddToCart() {
  if (!product.value) {
    return
  }
  if (!authStore.isAuthenticated) {
    await router.push({ name: 'login', query: { redirect: route.fullPath } })
    return
  }
  feedbackMessage.value = ''
  cartConfirmation.value = null
  try {
    const cart = await addCartItem(product.value.id, 1)
    uiStore.setCartCount(cart.totalCount)
    cartConfirmation.value = {
      title: product.value.title,
      totalCount: cart.totalCount,
    }
    feedbackMessage.value = '已加入购物车，现在可以去结算。'
    resetConfirmationTimer()
  } catch (error) {
    if (error instanceof Error && error.message.includes('请先登录')) {
      authStore.clear()
      await router.push({ name: 'login', query: { redirect: route.fullPath } })
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


