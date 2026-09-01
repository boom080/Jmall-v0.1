<template>
  <div class="my-products">
    <div class="page-header">
      <div>
        <h2>我的商品</h2>
        <p>草稿不会对买家公开；发布商品可随时继续编辑。</p>
      </div>
      <el-button type="primary" size="large" @click="$router.push('/merchant/products/new')">＋ 新建商品</el-button>
    </div>

    <el-alert v-if="notice" :title="notice" type="success" show-icon :closable="false" />
    <el-skeleton v-if="loading" :rows="5" animated />
    <el-empty v-else-if="!products.length" description="还没有商品，先创建一份草稿吧">
      <el-button type="primary" @click="$router.push('/merchant/products/new')">创建第一件商品</el-button>
    </el-empty>
    <div v-else class="product-list">
      <el-card v-for="product in products" :key="product.id" shadow="hover" class="product-row">
        <img :src="getProductImage(product.images, product.category)" :alt="product.title" referrerpolicy="no-referrer" />
        <div class="product-main">
          <div class="product-title-line">
            <strong>{{ product.title || '未命名商品' }}</strong>
            <el-tag :type="product.status === 'published' ? 'success' : 'info'">
              {{ product.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </div>
          <p>{{ product.description || '尚未填写商品详情' }}</p>
          <span>¥{{ (product.price / 100).toFixed(2) }} · {{ product.category || '未选择品类' }}</span>
        </div>
        <div class="row-actions">
          <el-button type="primary" plain @click="$router.push(`/merchant/products/${product.id}`)">编辑</el-button>
          <el-button v-if="product.status === 'published'" @click="$router.push(`/shop/product/${product.id}`)">查看商品</el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { productApi } from '@/services/products'
import { getProductImage } from '@/services/imageUtils'
import type { Product } from '@/types'

const route = useRoute()
const loading = ref(true)
const products = ref<Product[]>([])
const notice = computed(() => {
  if (route.query.notice === 'drafted') return '草稿已保存，买家暂时看不到这件商品。'
  if (route.query.notice === 'unpublished') return '商品已下架并转为草稿。'
  if (route.query.notice === 'updated') return '已发布商品修改成功。'
  return ''
})

onMounted(async () => {
  try {
    products.value = (await productApi.getMyProducts(1, 100)).records
  } catch (error: any) {
    ElMessage.error(error?.message || '商品列表加载失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.my-products { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 24px; margin-bottom: 20px; }
.page-header h2 { margin: 0 0 6px; }
.page-header p { margin: 0; color: #909399; }
.product-list { display: grid; gap: 14px; margin-top: 18px; }
.product-row :deep(.el-card__body) { display: flex; align-items: center; gap: 18px; }
.product-row img { width: 92px; height: 92px; flex: 0 0 auto; border-radius: 12px; object-fit: cover; background: #f5f7fa; }
.product-main { min-width: 0; flex: 1; }
.product-title-line { display: flex; align-items: center; gap: 10px; }
.product-title-line strong { overflow: hidden; font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.product-main p { overflow: hidden; margin: 9px 0; color: #606266; text-overflow: ellipsis; white-space: nowrap; }
.product-main span { color: #909399; font-size: 13px; }
.row-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; }
@media (max-width: 760px) { .product-row :deep(.el-card__body) { align-items: flex-start; flex-wrap: wrap; } .row-actions { width: 100%; } }
</style>
