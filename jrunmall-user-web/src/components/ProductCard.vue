<template>
  <article class="product-card">
    <img :src="product.coverUrl" :alt="product.title" class="product-card__image" />
    <div class="product-card__body">
      <p class="product-card__category">{{ product.category }}</p>
      <h3>{{ product.title }}</h3>
      <p class="product-card__subtitle">{{ product.subtitle }}</p>
      <ul class="product-card__points">
        <li v-for="point in product.sellingPoints.slice(0, 3)" :key="point">
          {{ point }}
        </li>
      </ul>
      <div class="product-card__footer">
        <strong>￥{{ product.price }}</strong>
        <div class="product-card__actions">
          <button type="button" class="card-action" @click="$emit('add-to-cart', product.id)">加入购物车</button>
          <RouterLink :to="`/products/${product.id}`">查看详情</RouterLink>
        </div>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import type { CatalogProduct } from '@/types/product'

defineEmits<{
  (event: 'add-to-cart', productId: number): void
}>()

defineProps<{
  product: CatalogProduct
}>()
</script>


