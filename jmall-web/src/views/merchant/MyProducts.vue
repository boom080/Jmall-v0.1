<template>
  <div class="my-products merchant-page">
    <section class="products-hero" aria-labelledby="my-products-title">
      <span class="hero-shape hero-shape-one" aria-hidden="true"></span>
      <span class="hero-shape hero-shape-two" aria-hidden="true"></span>
      <div class="products-hero-copy">
        <div class="eyebrow"><span>✦</span> MY PRODUCT COLLECTION</div>
        <h2 id="my-products-title">我的商品背包</h2>
        <p>每一件好物，都是你经营小店时收集到的闪亮灵感。</p>
        <div class="collection-numbers" aria-label="商品统计">
          <span><strong>{{ products.length }}</strong> 全部</span>
          <span><strong>{{ publishedCount }}</strong> 已发布</span>
          <span><strong>{{ draftCount }}</strong> 草稿</span>
        </div>
      </div>
      <div class="products-hero-mascot" aria-hidden="true">
        <JmallMascot variant="wave" :size="112" :animated="true" />
        <span>继续收集好物吧！</span>
      </div>
      <el-button type="primary" size="large" class="new-product-button" @click="$router.push('/merchant/products/new')">
        <span aria-hidden="true">＋</span> 新建商品
      </el-button>
    </section>

    <el-alert v-if="notice" :title="notice" type="success" show-icon :closable="false" class="page-notice" />

    <section v-if="!loading" class="inventory-toolbar" aria-label="商品筛选与完成度">
      <div class="inventory-progress">
        <div class="progress-copy">
          <div><span class="section-kicker">SHOP COLLECTION</span><strong>小店图鉴完成度</strong></div>
          <b>{{ collectionProgress }}%</b>
        </div>
        <div class="progress-track" role="progressbar" :aria-valuenow="collectionProgress" aria-valuemin="0" aria-valuemax="100">
          <span :style="{ width: `${collectionProgress}%` }"></span>
        </div>
        <small>{{ publishedCount }} 件已经和买家见面 · {{ draftCount }} 份草稿等待打磨</small>
      </div>
      <div class="filter-tabs" role="tablist" aria-label="商品状态筛选">
        <button
          v-for="filter in filters"
          :key="filter.key"
          type="button"
          class="filter-tab"
          :class="{ active: activeFilter === filter.key }"
          role="tab"
          :aria-selected="activeFilter === filter.key"
          @click="activeFilter = filter.key"
        >
          {{ filter.label }} <span>{{ filterCount(filter.key) }}</span>
        </button>
      </div>
    </section>

    <el-skeleton v-if="loading" :rows="5" animated class="product-skeleton" />
    <el-empty
      v-else-if="!filteredProducts.length"
      :description="products.length ? '这个分类还没有商品，换个筛选看看吧' : '还没有商品，先创建一份草稿吧'"
      class="products-empty"
    >
      <el-button type="primary" @click="$router.push('/merchant/products/new')">
        {{ products.length ? '创建一件新商品' : '创建第一件商品' }}
      </el-button>
    </el-empty>

    <div v-else class="product-list">
      <el-card v-for="product in filteredProducts" :key="product.id" shadow="never" class="product-row">
        <div class="product-cover">
          <img :src="getProductImage(product.images, product.category)" :alt="product.title || '商品图片'" referrerpolicy="no-referrer" />
          <span class="status-ribbon" :class="product.status === 'published' ? 'is-published' : 'is-draft'">
            {{ product.status === 'published' ? '已发布' : '草稿' }}
          </span>
          <span class="cover-sparkle" aria-hidden="true">✦</span>
        </div>
        <div class="product-main">
          <div class="product-title-line">
            <strong :title="product.title">{{ product.title || '未命名商品' }}</strong>
            <el-tag :type="product.status === 'published' ? 'success' : 'info'" size="small">
              {{ product.status === 'published' ? '已发布' : '草稿' }}
            </el-tag>
          </div>
          <p class="product-subtitle">{{ product.subtitle || product.description || '还没有写副标题，继续完善让顾客更快了解它' }}</p>
          <div class="product-meta-line">
            <span class="product-price">¥{{ (product.price / 100).toFixed(2) }}</span>
            <span class="meta-divider">·</span>
            <span>{{ product.category || '未选择品类' }}</span>
            <span class="meta-divider">·</span>
            <span>{{ product.status === 'published' ? `${product.saleCount || 0} 件已售` : '尚未发布' }}</span>
          </div>
          <div class="quality-row">
            <span class="quality-label">资料完善度</span>
            <div class="quality-track" role="progressbar" :aria-valuenow="qualityFor(product).score" aria-valuemin="0" aria-valuemax="100">
              <span :class="`quality-${qualityFor(product).tone}`" :style="{ width: `${qualityFor(product).score}%` }"></span>
            </div>
            <b :class="`quality-text quality-${qualityFor(product).tone}`">{{ qualityFor(product).score }}%</b>
            <span class="quality-hint">{{ qualityFor(product).hint }}</span>
          </div>
        </div>
        <div class="row-actions">
          <el-button type="primary" plain @click="$router.push(`/merchant/products/${product.id}`)">
            {{ product.status === 'draft' ? '继续完善' : '编辑商品' }}
          </el-button>
          <el-button v-if="product.status === 'published'" @click="$router.push(`/shop/product/${product.id}`)">
            查看商品
          </el-button>
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
import JmallMascot from '@/components/brand/JmallMascot.vue'
import type { Product } from '@/types'

type ProductFilter = 'all' | 'published' | 'draft'
type QualityTone = 'good' | 'fair' | 'low'

const route = useRoute()
const loading = ref(true)
const products = ref<Product[]>([])
const activeFilter = ref<ProductFilter>('all')
const filters: Array<{ key: ProductFilter; label: string }> = [
  { key: 'all', label: '全部' },
  { key: 'published', label: '已发布' },
  { key: 'draft', label: '草稿' },
]

const notice = computed(() => {
  if (route.query.notice === 'drafted') return '草稿已保存，买家暂时看不到这件商品。'
  if (route.query.notice === 'unpublished') return '商品已下架并转为草稿。'
  if (route.query.notice === 'updated') return '已发布商品修改成功。'
  return ''
})

const publishedCount = computed(() => products.value.filter(product => product.status === 'published').length)
const draftCount = computed(() => products.value.filter(product => product.status === 'draft').length)
const collectionProgress = computed(() => {
  if (!products.value.length) return 0
  return Math.round((publishedCount.value / products.value.length) * 100)
})
const filteredProducts = computed(() => {
  if (activeFilter.value === 'all') return products.value
  return products.value.filter(product => product.status === activeFilter.value)
})

function filterCount(filter: ProductFilter): number {
  if (filter === 'all') return products.value.length
  return filter === 'published' ? publishedCount.value : draftCount.value
}

function qualityFor(product: Product): { score: number; tone: QualityTone; hint: string } {
  const imageProvided = Array.isArray(product.images)
    ? product.images.some(image => Boolean(String(image || '').trim()))
    : Boolean(String(product.images || '').trim())
  const fields = [
    Boolean(String(product.title || '').trim()),
    Boolean(String(product.subtitle || '').trim()),
    Boolean(String(product.description || '').trim()),
    Boolean(String(product.category || '').trim()),
    Number(product.price) > 0,
    imageProvided,
  ]
  const score = Math.round(fields.filter(Boolean).length / fields.length * 100)
  const tone: QualityTone = score >= 80 ? 'good' : score >= 50 ? 'fair' : 'low'
  const hint = score >= 100 ? '可以出发' : score >= 80 ? '很棒，快完成啦' : score >= 50 ? '再补一点信息' : '需要继续完善'
  return { score, tone, hint }
}

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
.my-products {
  --merchant-ink: #312b45;
  --merchant-muted: #8d879e;
  --merchant-pink: #f25d78;
  --merchant-pink-dark: #dc4967;
  --merchant-lavender: #7563c9;
  --merchant-mint: #6dcfaf;
  max-width: 1160px;
  margin: 0 auto;
  padding: 26px 28px 48px;
}

.products-hero { position: relative; display: grid; grid-template-columns: minmax(0, 1fr) 150px auto; align-items: center; min-height: 205px; overflow: hidden; padding: 27px 32px; border-radius: 28px; background: linear-gradient(118deg, #fff0f1 0%, #f8effb 58%, #eee9ff 100%); box-shadow: 0 16px 38px rgba(104, 84, 140, .1); }
.hero-shape { position: absolute; border: 1px solid rgba(137, 105, 177, .14); border-radius: 50%; pointer-events: none; }
.hero-shape-one { width: 310px; height: 310px; top: -176px; right: 122px; }
.hero-shape-two { width: 150px; height: 150px; right: -50px; bottom: -76px; border-color: rgba(242, 93, 120, .16); }
.products-hero-copy { position: relative; z-index: 1; min-width: 0; }
.eyebrow, .section-kicker { color: #dc4967; font-size: 11px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
.eyebrow { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.eyebrow span { color: #ffd76b; font-size: 17px; }
.products-hero h2 { margin: 0; color: var(--merchant-ink); font-size: clamp(28px, 4vw, 38px); font-weight: 850; letter-spacing: -.04em; }
.products-hero p { max-width: 470px; margin: 9px 0 15px; color: #766f88; font-size: 13px; line-height: 1.6; }
.collection-numbers { display: flex; flex-wrap: wrap; gap: 8px; }
.collection-numbers span { padding: 6px 10px; border: 1px solid rgba(255,255,255,.78); border-radius: 99px; color: #827991; background: rgba(255,255,255,.62); font-size: 11px; }
.collection-numbers strong { margin-right: 3px; color: var(--merchant-ink); font-size: 13px; }
.products-hero-mascot { position: relative; z-index: 1; display: flex; align-items: center; flex-direction: column; justify-content: center; }
.products-hero-mascot span { margin-top: -2px; padding: 4px 9px; border-radius: 99px; color: #a95774; background: rgba(255,255,255,.7); font-size: 10px; font-weight: 700; white-space: nowrap; }
.new-product-button { position: relative; z-index: 1; height: 42px; margin-left: 20px; border: none; border-radius: 14px; background: var(--merchant-pink); box-shadow: 0 8px 17px rgba(242, 93, 120, .22); font-weight: 700; }
.new-product-button:hover { border-color: var(--merchant-pink-dark); background: var(--merchant-pink-dark); }
.page-notice { margin-top: 16px; border-radius: 14px; }

.inventory-toolbar { display: flex; align-items: flex-end; justify-content: space-between; gap: 22px; margin-top: 20px; padding: 17px 19px; border: 1px solid #eee9f4; border-radius: 20px; background: #fff; box-shadow: 0 8px 22px rgba(73, 56, 93, .045); }
.inventory-progress { min-width: 260px; flex: 1; }
.progress-copy { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.progress-copy > div { display: flex; flex-direction: column; gap: 5px; }
.progress-copy strong { color: var(--merchant-ink); font-size: 14px; }
.progress-copy b { color: var(--merchant-pink); font-size: 23px; line-height: 1; }
.progress-track { height: 8px; overflow: hidden; margin-top: 10px; border-radius: 10px; background: #f0ebf4; }
.progress-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--merchant-pink), #a976d5); transition: width .3s ease; }
.inventory-progress small { display: block; margin-top: 7px; color: #a29aaa; font-size: 10px; }
.filter-tabs { display: flex; flex-wrap: wrap; gap: 5px; }
.filter-tab { padding: 8px 11px; border: 1px solid transparent; border-radius: 10px; color: #8f899d; background: transparent; cursor: pointer; font: inherit; font-size: 12px; font-weight: 700; transition: color .2s, background .2s; }
.filter-tab:hover { color: var(--merchant-pink); background: #fff4f5; }
.filter-tab.active { color: var(--merchant-pink-dark); background: #fff0f1; }
.filter-tab span { margin-left: 4px; color: #b0a8b8; font-size: 10px; }
.filter-tab.active span { color: var(--merchant-pink); }

.product-skeleton { margin-top: 20px; padding: 22px; border-radius: 22px; background: #fff; }
.products-empty { margin: 45px 0; padding: 30px; border-radius: 22px; background: rgba(255,255,255,.7); }
.product-list { display: grid; gap: 13px; margin-top: 18px; }
.product-row { overflow: hidden; border: 1px solid #eeeaf3; border-radius: 20px; background: #fff; box-shadow: 0 7px 19px rgba(73, 56, 93, .04); transition: transform .2s ease, box-shadow .2s ease; }
.product-row:hover { transform: translateY(-2px); box-shadow: 0 12px 28px rgba(73, 56, 93, .09); }
.product-row :deep(.el-card__body) { display: flex; align-items: center; gap: 18px; padding: 16px 18px; }
.product-cover { position: relative; width: 110px; height: 110px; flex: 0 0 auto; overflow: hidden; border-radius: 16px; background: #fff6f1; }
.product-cover img { display: block; width: 100%; height: 100%; object-fit: cover; }
.status-ribbon { position: absolute; top: 8px; left: 8px; padding: 4px 7px; border-radius: 7px; color: #fff; font-size: 10px; font-weight: 800; box-shadow: 0 3px 8px rgba(50, 35, 65, .15); }
.status-ribbon.is-published { background: #63b99a; }
.status-ribbon.is-draft { background: #a28acb; }
.cover-sparkle { position: absolute; right: 8px; bottom: 5px; color: #ffd76b; font-size: 17px; text-shadow: 0 2px 4px rgba(116, 88, 62, .18); }
.product-main { min-width: 0; flex: 1; }
.product-title-line { display: flex; align-items: center; gap: 9px; min-width: 0; }
.product-title-line strong { overflow: hidden; color: #3f394f; font-size: 16px; text-overflow: ellipsis; white-space: nowrap; }
.product-title-line :deep(.el-tag) { flex: 0 0 auto; border: none; border-radius: 8px; font-size: 10px; }
.product-subtitle { overflow: hidden; margin: 8px 0 10px; color: #827b8e; font-size: 12px; line-height: 1.5; text-overflow: ellipsis; white-space: nowrap; }
.product-meta-line { display: flex; align-items: center; gap: 7px; color: #9a92a4; font-size: 11px; }
.product-price { color: #eb5a64; font-size: 17px; font-weight: 850; }
.meta-divider { color: #c9c0ce; }
.quality-row { display: flex; align-items: center; gap: 7px; margin-top: 13px; }
.quality-label { color: #93899e; font-size: 10px; white-space: nowrap; }
.quality-track { width: 94px; height: 6px; overflow: hidden; border-radius: 9px; background: #f0ebf2; }
.quality-track span { display: block; height: 100%; border-radius: inherit; }
.quality-good { color: #48a181; background: #66c3a2; }
.quality-fair { color: #c89244; background: #efbe61; }
.quality-low { color: #d36f83; background: #e893a3; }
.quality-text { font-size: 10px; }
.quality-hint { overflow: hidden; color: #aca3b3; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.row-actions { display: flex; flex: 0 0 auto; flex-wrap: wrap; justify-content: flex-end; gap: 8px; }
.row-actions :deep(.el-button) { margin: 0; border-radius: 11px; font-size: 12px; font-weight: 700; }
.row-actions :deep(.el-button--primary.is-plain) { color: var(--merchant-pink-dark); border-color: #f7bec5; background: #fff8f8; }

@media (prefers-reduced-motion: reduce) { .product-row { transition: none; } }
@media (max-width: 800px) {
  .my-products { padding: 18px 16px 38px; }
  .products-hero { grid-template-columns: minmax(0, 1fr) 120px; padding: 24px 22px; }
  .new-product-button { grid-column: 1 / -1; width: 100%; margin: 15px 0 0; }
  .products-hero-mascot { grid-column: 2; grid-row: 1; }
  .products-hero-mascot :deep(.jmall-mascot) { transform: scale(.8); }
  .inventory-toolbar { align-items: stretch; flex-direction: column; gap: 16px; }
  .filter-tabs { justify-content: flex-start; }
  .product-row :deep(.el-card__body) { align-items: flex-start; flex-wrap: wrap; }
  .row-actions { width: 100%; justify-content: flex-start; padding-left: 128px; }
}
@media (max-width: 520px) {
  .products-hero { display: block; }
  .products-hero-mascot { position: absolute; top: 13px; right: -1px; transform: scale(.72); transform-origin: top right; }
  .products-hero h2 { font-size: 29px; }
  .product-cover { width: 78px; height: 78px; }
  .product-row :deep(.el-card__body) { gap: 12px; padding: 13px; }
  .row-actions { padding-left: 90px; }
  .quality-row { flex-wrap: wrap; }
  .quality-hint { width: 100%; }
}
</style>
