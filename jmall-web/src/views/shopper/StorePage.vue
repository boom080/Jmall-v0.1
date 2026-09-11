<template>
  <div class="store-page">
    <div v-if="loading" class="loading-state">
      <div class="store-loading-banner shimmer"></div>
      <div class="store-loading-grid">
        <span v-for="index in 6" :key="index" class="shimmer"></span>
      </div>
    </div>

    <el-result
      v-else-if="error"
      class="store-result"
      icon="error"
      title="店铺暂时迷路了"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push('/shop')">🛒 去逛逛</el-button>
      </template>
    </el-result>

    <template v-else-if="store">
      <div v-if="isOwnStore" class="store-toolbar">
        <el-button type="primary" plain @click="backToMerchantCenter">← 返回商家中心</el-button>
      </div>

      <nav class="store-breadcrumb" aria-label="当前位置">
        <button type="button" @click="router.push('/shop')">好物货架</button>
        <span>/</span>
        <span>{{ store.name }}</span>
      </nav>

      <section class="store-banner">
        <div class="banner-shape shape-one" aria-hidden="true"></div>
        <div class="banner-shape shape-two" aria-hidden="true"></div>
        <div class="store-mascot">
          <div class="mascot-bubble">欢迎来我家逛逛！</div>
          <JmallMascot variant="wave" :size="128" label="Jmall 吉祥物" />
        </div>
        <div class="store-info">
          <div class="store-eyebrow"><span></span> Jmall 好物小店</div>
          <div class="store-title-row">
            <h1>{{ store.name }}</h1>
            <span class="store-level">Lv.{{ storeLevel }} 店铺</span>
          </div>
          <p class="store-category">✿ {{ store.category || '综合好物' }}</p>
          <p class="store-desc">{{ store.description || '这个商家正在认真准备更多好物，先来看看已经上架的吧。' }}</p>
          <div class="store-stats">
            <div><strong>{{ formatCount(storeStats.totalSales) }}</strong><span>累计售出</span></div>
            <div><strong>{{ formatCount(storeStats.productCount) }}</strong><span>在售商品</span></div>
            <div><strong>{{ formatCount(storeStats.totalOrders) }}</strong><span>有效订单</span></div>
          </div>
        </div>
        <div class="level-card">
          <span class="level-caption">店铺成长值</span>
          <div class="level-number">Lv.<strong>{{ storeLevel }}</strong></div>
          <div class="level-track"><i :style="{ width: `${levelProgress}%` }"></i></div>
          <span class="level-next">距离 Lv.{{ storeLevel + 1 }} 还有一点点</span>
        </div>
      </section>

      <section class="store-mission" aria-label="店铺浏览任务">
        <div class="mission-star">✦</div>
        <div>
          <strong>逛逛这家小店</strong>
          <p>发现 2 件商品，收集一份店铺灵感</p>
        </div>
        <span class="mission-progress"><i :style="{ width: `${Math.min(100, visitedIds.length / 2 * 100)}%` }"></i></span>
        <span class="mission-count">{{ Math.min(2, visitedIds.length) }}/2</span>
        <JmallMascot variant="idle" :size="49" :animated="false" />
      </section>

      <section class="store-products">
        <div class="products-heading">
          <div>
            <span>THE SHELF</span>
            <h2>店铺商品</h2>
          </div>
          <span class="products-count">{{ products.length }} 件在售</span>
        </div>
        <el-empty v-if="products.length === 0" description="暂无在售商品">
          <template #image><JmallMascot variant="idle" :size="88" :animated="false" /></template>
        </el-empty>
        <div v-else class="product-grid">
          <article
            v-for="product in products"
            :key="product.id"
            class="product-card"
            :class="{ visited: visitedIds.includes(product.id) }"
            @click="viewProduct(product.id)"
          >
            <div class="product-image-wrap">
              <img :src="productImage(product)" :alt="product.title" loading="lazy" @error="onImageError($event, product.category)" />
              <span class="product-rarity">{{ product.saleCount > 50 ? '人气好物' : '店主推荐' }}</span>
              <span class="product-heart">♡</span>
            </div>
            <div class="product-body">
              <div class="product-category">{{ product.category || '精选好物' }}</div>
              <h3 class="product-title">{{ product.title }}</h3>
              <p v-if="product.subtitle || product.description" class="product-subtitle">{{ product.subtitle || product.description }}</p>
              <div class="product-meta">
                <span>👁 {{ formatCount(product.viewCount) }}</span>
                <span>📦 {{ formatCount(product.saleCount) }} 已售</span>
              </div>
              <div class="product-footer">
                <span><small>¥</small>{{ formatPrice(product.price) }}</span>
                <b>去看看 →</b>
              </div>
            </div>
          </article>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import http from '@/services/http'
import { getCategoryPlaceholder, getProductImage } from '@/services/imageUtils'
import { useAuthStore } from '@/stores/auth'
import JmallMascot from '@/components/brand/JmallMascot.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const store = ref<any>(null)
const products = ref<any[]>([])
const loading = ref(true)
const error = ref<string | null>(null)
const storeStats = ref({ productCount: 0, totalSales: 0, totalOrders: 0 })
const STORE_VISITED_KEY = `jmall-v03-session-store-${String(route.params.storeId || 'unknown')}`
const visitedIds = ref<number[]>(loadVisitedIds())

function loadVisitedIds(): number[] {
  try {
    const stored = JSON.parse(sessionStorage.getItem(STORE_VISITED_KEY) || '[]')
    return Array.isArray(stored) ? stored.map(Number).filter(Number.isFinite) : []
  } catch { return [] }
}

const isOwnStore = computed(() => {
  const user = authStore.currentUser
  if (!user || !store.value) return false
  return Number(user.storeId) === Number(store.value.id) || Number(user.id) === Number(store.value.userId)
})

const storeLevel = computed(() => {
  const sales = Number(storeStats.value.totalSales || 0)
  if (sales >= 1000) return 5
  if (sales >= 300) return 4
  if (sales >= 100) return 3
  if (sales >= 30) return 2
  return 1
})

const levelProgress = computed(() => {
  const sales = Number(storeStats.value.totalSales || 0)
  const thresholds = [0, 30, 100, 300, 1000, 3000]
  const current = thresholds[storeLevel.value - 1]
  const next = thresholds[storeLevel.value] || thresholds[thresholds.length - 1]
  return Math.max(8, Math.min(100, ((sales - current) / Math.max(1, next - current)) * 100))
})

function backToMerchantCenter() { router.push({ name: 'merchant-dashboard' }) }

function formatPrice(value: number) { return ((value || 0) / 100).toFixed(2) }

function formatCount(value: number) {
  const count = value || 0
  if (count >= 10000) return `${(count / 10000).toFixed(1)}万`
  if (count >= 1000) return `${(count / 1000).toFixed(1)}k`
  return count.toString()
}

function productImage(product: any): string {
  return getProductImage(product?.images, product?.category)
}

function onImageError(event: Event, category?: string) {
  const image = event.target as HTMLImageElement
  if (image.dataset.fallbackApplied) return
  image.dataset.fallbackApplied = 'true'
  image.src = getCategoryPlaceholder(category)
}

function viewProduct(id: number) {
  if (!visitedIds.value.includes(id)) {
    visitedIds.value = [...visitedIds.value, id]
    sessionStorage.setItem(STORE_VISITED_KEY, JSON.stringify(visitedIds.value))
  }
  router.push(`/shop/product/${id}`)
}

onMounted(async () => {
  const storeId = route.params.storeId
  if (!storeId) {
    error.value = '缺少店铺ID'
    loading.value = false
    return
  }

  try {
    const [storeData, productData, statsData]: any[] = await Promise.all([
      http.get(`/stores/${storeId}`),
      http.get('/products', { params: { storeId, status: 'published', size: 50 } }),
      http.get(`/stores/${storeId}/stats`),
    ])
    store.value = storeData
    products.value = productData?.records || productData || []
    storeStats.value = statsData || storeStats.value
  } catch (e: any) {
    error.value = e.message || '加载店铺失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.store-page { --store-plum: #342b4a; --store-muted: #897e92; --store-line: #f0e3dd; --store-pink: #ff4d63; --store-coral: #ff6b81; max-width: 1300px; margin: 0 auto; padding: 24px 32px 78px; color: var(--store-plum); }
.store-toolbar { margin-bottom: 14px; }
.store-toolbar :deep(.el-button) { border-radius: 12px; color: #8a73c8; border-color: #ded5fa; background: #faf8ff; }
.store-breadcrumb { display: flex; align-items: center; gap: 9px; margin-bottom: 16px; color: #a69ca7; font-size: 12px; }
.store-breadcrumb button { padding: 0; border: 0; color: #8a74c8; background: transparent; cursor: pointer; font-size: 12px; font-weight: 700; }
.store-banner { position: relative; display: flex; align-items: center; gap: 22px; min-height: 270px; overflow: hidden; padding: 35px 36px 32px 42px; border: 1px solid rgba(255,255,255,.78); border-radius: 30px; color: var(--store-plum); background: linear-gradient(120deg, #fff0e5 0%, #ffe4ed 51%, #e7e4ff 100%); box-shadow: 0 17px 38px rgba(91, 65, 101, .1); }
.banner-shape { position: absolute; border: 1px dashed rgba(198,87,118,.27); border-radius: 50%; pointer-events: none; }
.shape-one { width: 310px; height: 160px; right: 17%; top: -94px; transform: rotate(-14deg); }
.shape-two { width: 220px; height: 130px; right: -20px; bottom: -74px; border-color: rgba(139,120,216,.33); transform: rotate(21deg); }
.store-mascot { position: relative; z-index: 1; display: grid; flex: 0 0 148px; place-items: center; align-self: stretch; }
.store-mascot :deep(.jmall-mascot) { filter: drop-shadow(0 13px 13px rgba(198,87,118,.19)); }
.mascot-bubble { position: absolute; z-index: 3; top: 6px; left: -20px; padding: 8px 11px; border-radius: 13px 13px 13px 4px; color: #fff; background: var(--store-plum); box-shadow: 0 7px 14px rgba(52,43,74,.15); font-size: 11px; font-weight: 800; white-space: nowrap; }
.store-info { position: relative; z-index: 1; min-width: 0; flex: 1; }
.store-eyebrow { display: flex; align-items: center; gap: 7px; color: #ac6f82; font-size: 11px; font-weight: 800; letter-spacing: .11em; }
.store-eyebrow span { width: 7px; height: 7px; border-radius: 50%; background: var(--store-coral); box-shadow: 0 0 0 4px rgba(255,107,129,.12); }
.store-title-row { display: flex; align-items: center; flex-wrap: wrap; gap: 11px; margin: 9px 0 5px; }
.store-title-row h1 { margin: 0; color: var(--store-plum); font-size: clamp(25px, 3.1vw, 34px); letter-spacing: -.045em; }
.store-level { padding: 5px 9px; border-radius: 999px; color: #765fc3; background: #f0ebff; font-size: 11px; font-weight: 800; }
.store-category { margin: 0 0 8px; color: #a07185; font-size: 12px; }
.store-desc { max-width: 540px; margin: 0 0 20px; color: #756d7c; font-size: 13px; line-height: 1.65; }
.store-stats { display: flex; gap: 29px; }
.store-stats div { display: grid; gap: 3px; }
.store-stats strong { color: var(--store-plum); font-size: 19px; letter-spacing: -.03em; }
.store-stats span { color: #998f9c; font-size: 10px; }
.level-card { position: relative; z-index: 1; flex: 0 0 155px; padding: 17px 16px; border: 1px solid rgba(255,255,255,.8); border-radius: 17px; background: rgba(255,255,255,.6); }
.level-caption, .level-next { display: block; color: #9d8d9d; font-size: 10px; }
.level-number { margin: 8px 0 13px; color: #8c71d0; font-size: 17px; font-weight: 800; }
.level-number strong { font-size: 34px; line-height: .8; }
.level-track { display: block; height: 7px; margin-bottom: 8px; overflow: hidden; border-radius: 99px; background: rgba(216,201,249,.72); }
.level-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #ab96e8, #ff8a9a); transition: width .35s ease; }
.level-next { white-space: nowrap; }
.store-mission { display: flex; align-items: center; gap: 13px; min-height: 76px; margin: 18px 0 31px; padding: 12px 19px; border: 1px solid #f3e4c8; border-radius: 19px; background: linear-gradient(100deg, #fffaf0, #fff6e9); }
.mission-star { display: grid; width: 38px; height: 38px; place-items: center; border-radius: 12px; color: #a87018; background: #ffedaa; font-size: 21px; }
.store-mission > div:nth-child(2) { min-width: 185px; }
.store-mission strong { font-size: 13px; }
.store-mission p { margin: 3px 0 0; color: var(--store-muted); font-size: 11px; }
.mission-progress { display: block; flex: 1; max-width: 310px; height: 7px; overflow: hidden; border-radius: 99px; background: #f2e4cb; }
.mission-progress i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #ffbd65, #ff6b81); transition: width .35s ease; }
.mission-count { color: #a77a38; font-size: 11px; font-weight: 800; }
.store-mission > :last-child { align-self: flex-end; margin-bottom: -5px; }
.products-heading { display: flex; align-items: end; justify-content: space-between; margin-bottom: 16px; }
.products-heading > div > span { color: #c19aaa; font-size: 10px; font-weight: 800; letter-spacing: .18em; }
.products-heading h2 { margin: 4px 0 0; font-size: 25px; letter-spacing: -.04em; }
.products-count { color: #a89da9; font-size: 12px; }
.product-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
.product-card { overflow: hidden; border: 1px solid rgba(238,227,222,.92); border-radius: 21px; background: #fff; box-shadow: 0 8px 19px rgba(75,54,73,.06); cursor: pointer; transition: transform .24s ease, box-shadow .24s ease, border-color .24s ease; }
.product-card:hover, .product-card.visited { border-color: #f3c3ca; box-shadow: 0 14px 27px rgba(113,76,104,.13); transform: translateY(-4px); }
.product-image-wrap { position: relative; height: 204px; overflow: hidden; background: #fff4ec; }
.product-image-wrap img { display: block; width: 100%; height: 100%; object-fit: cover; transition: transform .4s ease; }
.product-card:hover img { transform: scale(1.045); }
.product-rarity { position: absolute; top: 11px; left: 11px; padding: 5px 8px; border-radius: 999px; color: #9c682b; background: rgba(255,238,184,.92); font-size: 10px; font-weight: 800; }
.product-heart { position: absolute; right: 11px; bottom: 10px; display: grid; width: 32px; height: 32px; place-items: center; border: 1px solid rgba(255,255,255,.86); border-radius: 50%; color: #fff; background: rgba(52,43,74,.45); font-size: 20px; backdrop-filter: blur(6px); }
.product-body { display: flex; min-height: 190px; flex-direction: column; padding: 14px 15px 13px; }
.product-category { margin-bottom: 6px; color: #a267a0; font-size: 10px; font-weight: 800; }
.product-title { display: -webkit-box; overflow: hidden; margin: 0 0 6px; color: var(--store-plum); font-size: 16px; line-height: 1.42; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.product-subtitle { display: -webkit-box; overflow: hidden; margin: 0 0 9px; color: #928994; font-size: 12px; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.product-meta { display: flex; gap: 10px; margin-top: auto; color: #aaa1ac; font-size: 10px; }
.product-footer { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; margin-top: 9px; }
.product-footer > span { color: var(--store-pink); font-size: 23px; font-weight: 900; letter-spacing: -.04em; }
.product-footer small { margin-right: 2px; font-size: 13px; }
.product-footer b { color: #8a75ce; font-size: 10px; }
.loading-state { padding: 20px 0; }
.store-loading-banner { height: 270px; border-radius: 30px; background: #f7eee9; }
.store-loading-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 31px; }
.store-loading-grid span { height: 300px; border-radius: 21px; background: #f7eee9; }
.shimmer { background: linear-gradient(90deg, #f7eee9 25%, #fff8f3 37%, #f7eee9 63%) !important; background-size: 400% 100% !important; animation: shimmer 1.4s ease infinite; }
@keyframes shimmer { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
.store-result { margin: 35px 0; padding: 50px 0; border-radius: 24px; background: rgba(255,255,255,.8); }

@media (max-width: 1050px) {
  .store-page { padding-right: 22px; padding-left: 22px; }
  .store-banner { padding-right: 27px; padding-left: 28px; }
  .product-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .store-loading-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 780px) {
  .store-banner { align-items: flex-start; flex-wrap: wrap; padding: 27px 23px 23px; }
  .store-mascot { position: absolute; right: -10px; bottom: -14px; opacity: .25; transform: scale(.9); transform-origin: bottom right; }
  .mascot-bubble { display: none; }
  .store-info { width: 100%; flex: 1 1 100%; }
  .level-card { flex: 1 1 180px; max-width: 220px; }
  .store-mission > :last-child { display: none; }
  .product-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .store-loading-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 500px) {
  .store-page { padding: 14px 14px 65px; }
  .store-banner { min-height: 350px; border-radius: 24px; }
  .store-stats { gap: 17px; }
  .store-stats strong { font-size: 17px; }
  .store-mission { gap: 9px; padding: 11px; }
  .store-mission > div:nth-child(2) { min-width: 0; flex: 1; }
  .mission-progress { max-width: 100px; }
  .products-heading h2 { font-size: 22px; }
  .product-grid { gap: 12px; }
  .product-image-wrap { height: 150px; }
  .product-body { min-height: 194px; padding: 12px 11px; }
  .product-title { font-size: 14px; }
  .product-subtitle { font-size: 11px; }
  .product-meta { gap: 4px; font-size: 9px; }
}

@media (prefers-reduced-motion: reduce) {
  .product-card, .product-image-wrap img, .level-track i, .mission-progress i, .shimmer { transition: none; animation: none; }
}
</style>
