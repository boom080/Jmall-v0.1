<template>
  <div class="publish-success">
    <el-result icon="success" title="商品发布成功" sub-title="发布门禁已通过，商品现在已对买家可见。">
      <template #extra>
        <el-card v-if="product" shadow="never" class="product-preview">
          <img :src="getProductImage(product.images, product.category)" :alt="product.title" referrerpolicy="no-referrer" />
          <div>
            <el-tag type="success">已发布</el-tag>
            <h3>{{ product.title }}</h3>
            <p>¥{{ (product.price / 100).toFixed(2) }} · {{ product.category }}</p>
          </div>
        </el-card>
        <div class="success-actions">
          <el-button type="primary" @click="$router.push(`/shop/product/${productId}`)">查看商品</el-button>
          <el-button @click="$router.push(`/merchant/products/${productId}`)">继续编辑</el-button>
          <el-button @click="$router.push('/merchant/products')">返回我的店铺</el-button>
        </div>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { productApi } from '@/services/products'
import { getProductImage } from '@/services/imageUtils'
import type { Product } from '@/types'

const route = useRoute()
const productId = Number(route.params.id)
const product = ref<Product | null>(null)

onMounted(async () => {
  try { product.value = await productApi.get(productId, false) } catch { /* actions remain available */ }
})
</script>

<style scoped>
.publish-success { max-width: 760px; margin: 36px auto; }
.product-preview { margin: 0 auto 24px; text-align: left; }
.product-preview :deep(.el-card__body) { display: flex; align-items: center; gap: 18px; }
.product-preview img { width: 112px; height: 112px; border-radius: 14px; object-fit: cover; background: #f5f7fa; }
.product-preview h3 { margin: 10px 0 6px; }
.product-preview p { margin: 0; color: #606266; }
.success-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }
.success-actions .el-button { margin-left: 0; }
</style>
