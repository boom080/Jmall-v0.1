<template>
  <div v-if="loading" class="detail-state detail-loading">
    <div class="detail-skeleton-image shimmer"></div>
    <div class="detail-skeleton-copy">
      <span class="shimmer"></span>
      <span class="shimmer wide"></span>
      <span class="shimmer"></span>
      <span class="shimmer price"></span>
    </div>
  </div>

  <el-result
    v-else-if="error"
    class="detail-state-result"
    icon="error"
    title="好物暂时迷路了"
    :sub-title="error"
  >
    <template #extra>
      <el-button type="primary" @click="loadProduct">🔄 再试一次</el-button>
    </template>
  </el-result>

  <el-result
    v-else-if="!product"
    class="detail-state-result"
    icon="warning"
    title="商品不存在"
    sub-title="该商品可能已下架或不存在"
  >
    <template #extra>
      <el-button type="primary" @click="$router.push('/shop')">🛒 浏览其他商品</el-button>
    </template>
  </el-result>

  <div v-else class="product-detail">
    <nav class="detail-breadcrumb" aria-label="当前位置">
      <button type="button" @click="router.back()">← 返回好物货架</button>
      <span>/</span>
      <span>{{ product.category || '精选好物' }}</span>
    </nav>

    <section class="detail-main">
      <div class="detail-gallery">
        <div class="gallery-main">
          <img
            :src="activeImage || getProductImage(product.images, product.category)"
            :alt="product.title"
            @error="onImageError"
          />
          <span class="gallery-sticker">✦ 今日发现</span>
          <span class="gallery-corner" aria-hidden="true">♡</span>
        </div>
        <div v-if="imageList.length > 1" class="gallery-thumbs" aria-label="商品图片">
          <button
            v-for="(image, index) in imageList"
            :key="`${image}-${index}`"
            type="button"
            :class="{ active: activeImage === image }"
            @click="activeImage = image"
          >
            <img :src="image" :alt="`${product.title} 图片 ${index + 1}`" @error="onThumbError($event)" />
          </button>
        </div>
      </div>

      <div class="detail-info">
        <div class="detail-labels">
          <span class="style-badge">{{ styleLabel(product.style) || '精选风格' }}</span>
          <span class="fresh-badge">新发现</span>
        </div>
        <h1>{{ product.title }}</h1>
        <p v-if="product.subtitle" class="subtitle">{{ product.subtitle }}</p>
        <p v-else class="subtitle-empty">商家还没有填写副标题</p>
        <p class="category">{{ product.category || '精选好物' }}</p>

        <div class="price-section">
          <span class="price-currency">¥</span>
          <span class="price">{{ formatPrice(product.price) }}</span>
          <span class="price-note">好物价</span>
        </div>

        <div class="coin-callout">
          <JmallMascot variant="mark" :size="42" :animated="false" />
          <div>
            <strong>好物灵感夹</strong>
            <span>收藏或加入购物车，记录你的好物灵感</span>
          </div>
          <span class="coin">♡</span>
        </div>

        <div class="stats" aria-label="商品数据">
          <span><strong>{{ formatViews(product.viewCount) }}</strong> 次浏览</span>
          <span><strong>{{ formatViews(product.likeCount) }}</strong> 点赞</span>
          <span><strong>{{ formatViews(product.saleCount) }}</strong> 已售</span>
        </div>

        <div v-if="sellingPoints.length" class="selling-points">
          <div class="selling-heading"><span>AI 店员划重点</span><i></i></div>
          <span v-for="point in sellingPoints" :key="point">✓ {{ point }}</span>
        </div>

        <button v-if="product.storeName && product.storeId" type="button" class="store-strip" @click="router.push(`/store/${product.storeId}`)">
          <span class="store-avatar">🏪</span>
          <span class="store-copy"><small>来自店铺</small><strong>{{ product.storeName }}</strong></span>
          <span class="store-arrow">去逛逛 →</span>
        </button>

        <div class="actions">
          <el-button type="primary" size="large" class="cart-button" @click="addToCart" :loading="addingToCart" :disabled="isOwnProduct">
            {{ isOwnProduct ? '这是你自己的商品' : '🛒 加入购物车' }}
          </el-button>
          <el-button size="large" class="collect-button" :class="{ collected }" @click="toggleCollect">
            <span>{{ collected ? '♥' : '♡' }}</span>{{ collected ? '已收藏' : '收藏' }}
          </el-button>
        </div>
      </div>
    </section>

    <section class="detail-content">
      <div class="content-heading">
        <div>
          <span>DETAILS</span>
          <h2>商品说明</h2>
        </div>
        <span class="content-source">商家原文</span>
      </div>
      <div class="description">{{ product.description || product.aiDetail || '商家暂未填写详细说明' }}</div>
      <div class="honest-note">
        <span>i</span>
        <p>以上信息来自商家填写内容及 AI 整理，仅供浏览参考；材质、规格、功效与售后以实际商品和店铺说明为准。</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { productApi, cartApi } from '@/services/products'
import http from '@/services/http'
import { getCategoryPlaceholder, getProductImage } from '@/services/imageUtils'
import JmallMascot from '@/components/brand/JmallMascot.vue'
import type { Product } from '@/types'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const product = ref<Product | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const addingToCart = ref(false)
const collected = ref(false)
const activeImage = ref('')

const imageList = computed(() => {
  const raw = product.value?.images
  if (Array.isArray(raw)) return raw.map(String).filter(Boolean)
  if (typeof raw !== 'string' || !raw.trim()) return []
  const value = raw.trim()
  if (value.startsWith('[')) {
    try {
      const parsed = JSON.parse(value)
      if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean)
    } catch { /* fall through to legacy comma-separated values */ }
  }
  return value.split(',').map(item => item.trim()).filter(Boolean)
})

const sellingPoints = computed(() => {
  const raw = product.value?.aiSellingPoints
  if (Array.isArray(raw)) return raw.map(String).filter(Boolean).slice(0, 5)
  if (typeof raw !== 'string' || !raw.trim()) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.map(String).filter(Boolean).slice(0, 5) : []
  } catch { return [] }
})

const isOwnProduct = computed(() => Boolean(
  (authStore.currentUser?.storeId && product.value?.storeId === authStore.currentUser.storeId)
  || (product.value?.purchasable === false
      && product.value?.unavailableReason?.includes('自己店铺'))
))

function formatPrice(value: number) { return ((value || 0) / 100).toFixed(2) }

function formatViews(value: number) {
  const count = value || 0
  return count >= 10000 ? `${(count / 10000).toFixed(1)}万` : count.toLocaleString()
}

function styleLabel(style: string) {
  const labels: Record<string, string> = { pinduoduo: '拼多多风', taobao: '淘宝风', jd: '京东风', suning: '苏宁风', xiaohongshu: '小红书风' }
  return labels[style] || ''
}

async function addToCart() {
  if (!authStore.isAuthenticated) { router.push('/login'); return }
  if (isOwnProduct.value) { ElMessage.warning('不能购买自己店铺的商品'); return }
  addingToCart.value = true
  try {
    await cartApi.add(product.value!.id, 1)
    ElMessage.success('已加入购物车，等你随时回来')
  } catch (e: any) { ElMessage.error(e.message || '加入购物车失败') }
  finally { addingToCart.value = false }
}

async function toggleCollect() {
  if (!authStore.isAuthenticated) { router.push('/login'); return }
  try {
    if (collected.value) {
      await http.delete(`/collections/${product.value!.id}`)
      collected.value = false
      ElMessage.success('已取消收藏')
    } else {
      await http.post(`/collections/${product.value!.id}`)
      collected.value = true
      ElMessage.success('已加入收藏')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '操作失败')
  }
}

function onImageError(event: Event) {
  const image = event.target as HTMLImageElement
  if (image.dataset.fallbackApplied) return
  image.dataset.fallbackApplied = 'true'
  image.src = getCategoryPlaceholder(product.value?.category)
}

function onThumbError(event: Event) {
  const image = event.target as HTMLImageElement
  image.style.visibility = 'hidden'
}

onMounted(() => { loadProduct() })

async function loadProduct() {
  loading.value = true
  error.value = null
  try {
    product.value = await productApi.get(Number(route.params.id))
    activeImage.value = imageList.value[0] || ''
    if (authStore.isAuthenticated) {
      try {
        collected.value = await http.get(`/collections/check/${product.value!.id}`)
      } catch { /* collection status is optional */ }
    }
  } catch (e: any) {
    error.value = e.message || '加载商品信息失败'
    product.value = null
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.product-detail { --detail-plum: #342b4a; --detail-muted: #897e92; --detail-line: #f0e3dd; --detail-pink: #ff4d63; --detail-coral: #ff6b81; max-width: 1220px; margin: 0 auto; padding: 24px 32px 78px; color: var(--detail-plum); }
.detail-breadcrumb { display: flex; align-items: center; gap: 10px; margin: 0 0 16px; color: #aaa0aa; font-size: 12px; }
.detail-breadcrumb button { padding: 0; border: 0; color: #8a74c8; background: transparent; cursor: pointer; font-size: 12px; font-weight: 700; }
.detail-breadcrumb button:hover { color: var(--detail-pink); }
.detail-main { display: grid; grid-template-columns: minmax(390px, .95fr) minmax(390px, 1.05fr); gap: 50px; padding: 28px; border: 1px solid var(--detail-line); border-radius: 28px; background: rgba(255,255,255,.94); box-shadow: 0 14px 34px rgba(82, 56, 79, .075); }
.detail-gallery { min-width: 0; }
.gallery-main { position: relative; overflow: hidden; aspect-ratio: 1 / .92; border-radius: 20px; background: #fff2ed; }
.gallery-main img { display: block; width: 100%; height: 100%; object-fit: cover; }
.gallery-sticker { position: absolute; top: 15px; left: 15px; padding: 7px 11px; border-radius: 999px; color: #9a5f29; background: rgba(255, 242, 199, .9); font-size: 11px; font-weight: 800; }
.gallery-corner { position: absolute; right: 15px; bottom: 13px; display: grid; width: 37px; height: 37px; place-items: center; border-radius: 50%; color: #fff; background: rgba(52,43,74,.47); font-size: 22px; backdrop-filter: blur(6px); }
.gallery-thumbs { display: flex; gap: 10px; margin-top: 12px; overflow-x: auto; }
.gallery-thumbs button { flex: 0 0 61px; width: 61px; height: 61px; overflow: hidden; padding: 0; border: 2px solid transparent; border-radius: 11px; background: #fff4ef; cursor: pointer; }
.gallery-thumbs button.active { border-color: var(--detail-pink); box-shadow: 0 0 0 3px rgba(255,77,99,.1); }
.gallery-thumbs img { display: block; width: 100%; height: 100%; object-fit: cover; }
.detail-info { display: flex; min-width: 0; flex-direction: column; padding: 5px 5px 0 0; }
.detail-labels { display: flex; align-items: center; gap: 8px; }
.style-badge, .fresh-badge { padding: 6px 10px; border-radius: 999px; font-size: 11px; font-weight: 800; }
.style-badge { color: #7561bd; background: #f0ebff; }
.fresh-badge { color: #9e6b30; background: #fff1c7; }
.detail-info h1 { margin: 15px 0 7px; color: var(--detail-plum); font-size: clamp(26px, 3vw, 36px); line-height: 1.22; letter-spacing: -.045em; }
.subtitle { margin: 0; color: #756c7c; font-size: 16px; line-height: 1.6; }
.subtitle-empty { margin: 0; color: #b1a8b0; font-size: 13px; }
.category { margin: 11px 0 0; color: #a58f9c; font-size: 12px; }
.price-section { display: flex; align-items: baseline; gap: 3px; margin: 25px 0 17px; }
.price-currency { color: var(--detail-pink); font-size: 20px; font-weight: 900; }
.price { color: var(--detail-pink); font-size: 42px; font-weight: 900; letter-spacing: -.055em; }
.price-note { margin-left: 8px; padding: 4px 8px; border-radius: 6px; color: #b17836; background: #fff5da; font-size: 11px; }
.coin-callout { display: flex; align-items: center; gap: 8px; min-height: 62px; padding: 8px 12px 8px 8px; border: 1px solid #f5e2b7; border-radius: 16px; background: linear-gradient(95deg, #fffaf0, #fff5dd); }
.coin-callout :deep(.jmall-mascot) { flex: 0 0 42px; }
.coin-callout > div { display: grid; gap: 3px; min-width: 0; }
.coin-callout strong { color: #9b6725; font-size: 12px; }
.coin-callout span:not(.coin) { overflow: hidden; color: #ae926f; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.coin-callout .coin { margin-left: auto; font-size: 19px; }
.stats { display: flex; flex-wrap: wrap; gap: 20px; margin: 18px 0 17px; color: #a29aa4; font-size: 12px; }
.stats strong { margin-right: 2px; color: var(--detail-plum); font-size: 14px; }
.selling-points { padding: 14px; border: 1px solid #eee9ff; border-radius: 16px; background: #faf8ff; }
.selling-heading { display: flex; align-items: center; gap: 8px; margin-bottom: 9px; color: #765fc3; font-size: 12px; font-weight: 800; }
.selling-heading i { display: block; width: 28px; height: 1px; background: #d5c9f9; }
.selling-points > span { display: inline-block; margin: 0 6px 6px 0; padding: 5px 8px; border-radius: 7px; color: #7566a6; background: #f0ebff; font-size: 11px; }
.store-strip { display: flex; align-items: center; gap: 10px; margin-top: 16px; padding: 10px; border: 1px solid var(--detail-line); border-radius: 14px; text-align: left; color: var(--detail-plum); background: #fff; cursor: pointer; transition: border-color .2s, box-shadow .2s; }
.store-strip:hover { border-color: #efb6bf; box-shadow: 0 6px 14px rgba(255,77,99,.08); }
.store-avatar { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 11px; background: #fff2e4; font-size: 18px; }
.store-copy { display: grid; gap: 2px; flex: 1; min-width: 0; }
.store-copy small { color: #aaa1aa; font-size: 10px; }
.store-copy strong { overflow: hidden; color: #60546a; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.store-arrow { color: #8b75cc; font-size: 11px; font-weight: 800; white-space: nowrap; }
.actions { display: flex; gap: 10px; margin-top: auto; padding-top: 20px; }
.actions :deep(.el-button) { height: 48px; border-radius: 14px; font-weight: 800; }
.cart-button { flex: 1; border: 0; background: var(--detail-pink); box-shadow: 0 8px 16px rgba(255,77,99,.2); }
.cart-button:hover { background: #eb3f56; }
.collect-button { min-width: 100px; color: #857887; border-color: var(--detail-line); background: #fff; }
.collect-button.collected { color: var(--detail-pink); border-color: #f5c2c8; background: #fff2f4; }
.collect-button span { margin-right: 5px; font-size: 20px; vertical-align: -2px; }
.detail-content { margin-top: 22px; padding: 27px 30px 25px; border: 1px solid var(--detail-line); border-radius: 24px; background: rgba(255,255,255,.9); }
.content-heading { display: flex; align-items: center; justify-content: space-between; gap: 15px; padding-bottom: 18px; border-bottom: 1px solid #f3ece8; }
.content-heading > div > span { color: #c19aaa; font-size: 10px; font-weight: 800; letter-spacing: .18em; }
.content-heading h2 { margin: 4px 0 0; color: var(--detail-plum); font-size: 21px; }
.content-source { padding: 5px 9px; border-radius: 7px; color: #a69aa6; background: #faf5f1; font-size: 11px; }
.description { min-height: 100px; padding: 21px 0 12px; color: #675d6d; font-size: 15px; line-height: 2; white-space: pre-line; }
.honest-note { display: flex; align-items: flex-start; gap: 8px; padding: 11px 12px; border-radius: 11px; color: #9a8f96; background: #fbf8f6; font-size: 11px; line-height: 1.6; }
.honest-note > span { display: grid; flex: 0 0 17px; width: 17px; height: 17px; place-items: center; border: 1px solid #b7aab2; border-radius: 50%; color: #9a8f96; font-size: 11px; font-weight: 800; }
.honest-note p { margin: 0; }
.detail-state { max-width: 1100px; margin: 35px auto; padding: 30px; border: 1px solid var(--detail-line); border-radius: 26px; background: #fff; }
.detail-loading { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
.detail-skeleton-image { min-height: 430px; border-radius: 20px; background: #f7eee9; }
.detail-skeleton-copy { display: grid; align-content: center; gap: 17px; }
.detail-skeleton-copy span { display: block; width: 45%; height: 18px; border-radius: 9px; background: #f3e7e3; }
.detail-skeleton-copy span.wide { width: 90%; height: 38px; }
.detail-skeleton-copy span.price { width: 35%; height: 42px; margin-top: 20px; }
.shimmer { background: linear-gradient(90deg, #f7eee9 25%, #fff8f3 37%, #f7eee9 63%) !important; background-size: 400% 100% !important; animation: shimmer 1.4s ease infinite; }
@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
.detail-state-result { margin: 40px auto; padding: 45px 0; border-radius: 24px; background: rgba(255,255,255,.8); }

@media (max-width: 900px) {
  .product-detail { padding-right: 22px; padding-left: 22px; }
  .detail-main { grid-template-columns: minmax(0, 1fr); gap: 25px; }
  .detail-info { padding: 0; }
  .detail-skeleton-image { min-height: 320px; }
}

@media (max-width: 560px) {
  .product-detail { padding: 14px 14px 65px; }
  .detail-main { padding: 14px; border-radius: 22px; }
  .gallery-main { border-radius: 16px; }
  .detail-info h1 { font-size: 27px; }
  .price { font-size: 36px; }
  .coin-callout span:not(.coin) { white-space: normal; }
  .stats { gap: 11px; }
  .actions { position: sticky; bottom: 10px; z-index: 3; margin-right: -3px; margin-left: -3px; padding: 10px 3px 0; background: rgba(255,255,255,.9); backdrop-filter: blur(8px); }
  .detail-content { padding: 22px 17px; }
  .detail-loading { grid-template-columns: 1fr; gap: 20px; padding: 15px; }
  .detail-skeleton-image { min-height: 260px; }
}

@media (prefers-reduced-motion: reduce) {
  .shimmer, .store-strip { animation: none; transition: none; }
}
</style>
