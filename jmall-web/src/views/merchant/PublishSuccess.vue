<template>
  <div class="publish-success merchant-page">
    <section class="success-hero" aria-labelledby="publish-success-title">
      <span class="confetti confetti-one" aria-hidden="true">✦</span>
      <span class="confetti confetti-two" aria-hidden="true">✦</span>
      <span class="confetti confetti-three" aria-hidden="true">●</span>
      <div class="success-copy">
        <div class="eyebrow"><span>✦</span> QUEST COMPLETE</div>
        <h2 id="publish-success-title">商品发布成功</h2>
        <p>你的好物已经出现在店铺里，准备迎接第一位顾客吧！</p>
        <div class="reward-pills" aria-label="发布结果">
          <span><b>✦</b> 上架任务完成</span>
          <span><b>🛍️</b> 商品图鉴 +1 件</span>
        </div>
      </div>
      <div class="success-mascot">
        <JmallMascot variant="reward" :size="152" :animated="true" label="商品发布成功奖励动画" />
        <span>闪亮登场！</span>
      </div>
    </section>

    <section class="published-panel" aria-label="已发布商品信息">
      <div class="panel-heading">
        <div>
          <span class="section-kicker">JUST PUBLISHED</span>
          <h3>刚刚上架的好物</h3>
        </div>
        <span class="visible-chip"><i aria-hidden="true">●</i> 买家可见</span>
      </div>

      <el-card v-if="product" shadow="never" class="product-preview">
        <div class="preview-image-wrap">
          <img :src="getProductImage(product.images, product.category)" :alt="product.title || '商品图片'" referrerpolicy="no-referrer" />
          <span class="preview-sparkle" aria-hidden="true">✦</span>
        </div>
        <div class="preview-copy">
          <el-tag type="success" size="small">已发布</el-tag>
          <h3>{{ product.title || '未命名商品' }}</h3>
          <p v-if="product.subtitle" class="preview-subtitle">{{ product.subtitle }}</p>
          <p class="preview-meta">¥{{ (product.price / 100).toFixed(2) }} <span>·</span> {{ product.category || '未选择品类' }}</p>
        </div>
      </el-card>
      <div v-else class="preview-fallback">
        <JmallMascot variant="idle" :size="68" :animated="false" />
        <div><strong>商品已发布</strong><span>商品信息正在路上，下面的操作仍然可以继续。</span></div>
      </div>

      <div class="success-actions">
        <el-button type="primary" class="primary-action" @click="$router.push(`/shop/product/${productId}`)">
          查看商品 <span aria-hidden="true">↗</span>
        </el-button>
        <el-button class="secondary-action" @click="$router.push(`/merchant/products/${productId}`)">
          继续编辑
        </el-button>
        <el-button text class="back-action" @click="$router.push('/merchant/products')">
          返回我的店铺
        </el-button>
      </div>
    </section>

    <section class="next-quest">
      <div class="next-icon" aria-hidden="true">＋</div>
      <div><strong>再收集一件好物？</strong><span>继续完善你的商品图鉴，让小店一点点长大。</span></div>
      <el-button text type="primary" @click="$router.push('/merchant/products/new')">创建新商品 <span aria-hidden="true">→</span></el-button>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { productApi } from '@/services/products'
import { getProductImage } from '@/services/imageUtils'
import JmallMascot from '@/components/brand/JmallMascot.vue'
import type { Product } from '@/types'

const route = useRoute()
const productId = Number(route.params.id)
const product = ref<Product | null>(null)

onMounted(async () => {
  try { product.value = await productApi.get(productId, false) } catch { /* actions remain available */ }
})
</script>

<style scoped>
.publish-success {
  --merchant-ink: #312b45;
  --merchant-pink: #f25d78;
  --merchant-pink-dark: #dc4967;
  --merchant-lavender: #7563c9;
  --merchant-mint: #6dcfaf;
  max-width: 900px;
  margin: 0 auto;
  padding: 34px 28px 52px;
}

.success-hero { position: relative; display: grid; grid-template-columns: minmax(0, 1fr) 190px; align-items: center; min-height: 250px; overflow: hidden; padding: 31px 40px; border: 1px solid rgba(255,255,255,.7); border-radius: 30px; background: linear-gradient(120deg, #fff0f1 0%, #f8edfb 57%, #ede9ff 100%); box-shadow: 0 18px 45px rgba(104, 84, 140, .12); }
.success-hero::before { position: absolute; width: 270px; height: 270px; right: 44px; top: -141px; border: 1px solid rgba(137, 105, 177, .16); border-radius: 50%; content: ''; }
.success-hero::after { position: absolute; width: 120px; height: 120px; right: -32px; bottom: -60px; border: 1px solid rgba(242, 93, 120, .15); border-radius: 50%; content: ''; }
.success-copy { position: relative; z-index: 1; }
.eyebrow, .section-kicker { color: #dc4967; font-size: 11px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
.eyebrow { display: flex; align-items: center; gap: 8px; margin-bottom: 11px; }
.eyebrow span { color: #ffd76b; font-size: 17px; }
.success-copy h2 { margin: 0; color: var(--merchant-ink); font-size: clamp(29px, 4vw, 40px); font-weight: 850; letter-spacing: -.045em; }
.success-copy p { max-width: 455px; margin: 11px 0 19px; color: #756f88; font-size: 14px; line-height: 1.7; }
.reward-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.reward-pills span { padding: 7px 10px; border: 1px solid rgba(255,255,255,.8); border-radius: 99px; color: #887e92; background: rgba(255,255,255,.62); font-size: 11px; font-weight: 700; }
.reward-pills b { margin-right: 4px; color: var(--merchant-pink); }
.success-mascot { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.success-mascot::before { position: absolute; width: 130px; height: 90px; border-radius: 50%; background: rgba(242, 93, 120, .14); content: ''; filter: blur(14px); transform: translateY(20px); }
.success-mascot :deep(.jmall-mascot) { position: relative; }
.success-mascot > span { margin-top: -4px; padding: 5px 10px; border-radius: 99px; color: #a95774; background: rgba(255,255,255,.7); font-size: 10px; font-weight: 800; }
.confetti { position: absolute; z-index: 2; color: #ffd76b; font-size: 22px; pointer-events: none; }
.confetti-one { top: 28px; right: 210px; transform: rotate(17deg); }
.confetti-two { right: 25px; bottom: 68px; color: var(--merchant-mint); font-size: 17px; }
.confetti-three { top: 48px; left: 46%; color: #9a82d6; font-size: 12px; }

.published-panel { margin-top: 19px; padding: 23px 25px 24px; border: 1px solid #eee9f3; border-radius: 22px; background: #fff; box-shadow: 0 9px 25px rgba(73, 56, 93, .06); }
.panel-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.panel-heading h3 { margin: 5px 0 0; color: var(--merchant-ink); font-size: 18px; font-weight: 800; }
.visible-chip { padding: 6px 10px; border-radius: 99px; color: #4aa17e; background: #effaf4; font-size: 11px; font-weight: 800; white-space: nowrap; }
.visible-chip i { margin-right: 4px; color: #63c497; font-size: 9px; font-style: normal; }
.product-preview { margin-top: 18px; border: 1px solid #f1edf4; border-radius: 17px; background: #fffcfc; }
.product-preview :deep(.el-card__body) { display: flex; align-items: center; gap: 17px; padding: 13px; }
.preview-image-wrap { position: relative; width: 112px; height: 112px; flex: 0 0 auto; overflow: hidden; border-radius: 14px; background: #fff4f1; }
.preview-image-wrap img { display: block; width: 100%; height: 100%; object-fit: cover; }
.preview-sparkle { position: absolute; right: 8px; bottom: 5px; color: #ffd76b; font-size: 17px; text-shadow: 0 2px 4px rgba(116, 88, 62, .18); }
.preview-copy { min-width: 0; }
.preview-copy :deep(.el-tag) { border: none; border-radius: 8px; font-size: 10px; }
.preview-copy h3 { overflow: hidden; margin: 9px 0 5px; color: #40394f; font-size: 17px; text-overflow: ellipsis; white-space: nowrap; }
.preview-copy p { margin: 0; color: #968d9e; font-size: 12px; }
.preview-copy .preview-subtitle { overflow: hidden; max-width: 570px; margin-bottom: 7px; color: #82798c; text-overflow: ellipsis; white-space: nowrap; }
.preview-meta span { margin: 0 6px; color: #c4bac7; }
.preview-meta:first-letter { color: #eb5a64; }
.preview-fallback { display: flex; align-items: center; gap: 14px; min-height: 112px; margin-top: 18px; padding: 14px 18px; border: 1px dashed #e9dfec; border-radius: 17px; background: #fffcfc; }
.preview-fallback > div { display: flex; flex-direction: column; gap: 6px; }
.preview-fallback strong { color: #40394f; font-size: 14px; }
.preview-fallback span { color: #9c93a4; font-size: 11px; }
.success-actions { display: flex; flex-wrap: wrap; justify-content: center; gap: 9px; margin-top: 22px; }
.success-actions :deep(.el-button) { height: 40px; margin: 0; border-radius: 12px; font-size: 12px; font-weight: 800; }
.primary-action { border: none; background: var(--merchant-pink); box-shadow: 0 8px 16px rgba(242, 93, 120, .2); }
.primary-action:hover { border-color: var(--merchant-pink-dark); background: var(--merchant-pink-dark); }
.secondary-action { color: var(--merchant-lavender); border-color: #ddd6f2; background: #fbfaff; }
.secondary-action:hover { color: var(--merchant-lavender); border-color: #bcb0e1; background: #fff; }
.back-action { color: #9b91a5; }

.next-quest { display: flex; align-items: center; gap: 12px; margin-top: 17px; padding: 14px 16px; border: 1px solid #edf3ef; border-radius: 17px; background: linear-gradient(90deg, #f6fbf8, #fff); }
.next-icon { display: grid; width: 36px; height: 36px; flex: 0 0 auto; place-items: center; border-radius: 12px; color: #4ca486; background: #e7f6ee; font-size: 22px; }
.next-quest > div:nth-child(2) { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 3px; }
.next-quest strong { color: #496354; font-size: 12px; }
.next-quest span { overflow: hidden; color: #94a297; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.next-quest :deep(.el-button) { color: #4ca486; font-size: 12px; font-weight: 800; }

@media (prefers-reduced-motion: reduce) { .success-mascot :deep(.jmall-mascot) { animation: none; } }
@media (max-width: 650px) {
  .publish-success { padding: 18px 14px 38px; }
  .success-hero { display: block; min-height: 0; padding: 25px 22px 20px; }
  .success-copy { padding-right: 15px; }
  .success-copy h2 { font-size: 30px; }
  .success-mascot { position: absolute; top: 5px; right: -4px; transform: scale(.72); transform-origin: top right; }
  .success-mascot > span { display: none; }
  .published-panel { padding: 19px 15px 20px; }
  .product-preview :deep(.el-card__body) { align-items: flex-start; }
  .preview-image-wrap { width: 86px; height: 86px; }
  .preview-copy h3 { font-size: 15px; }
  .success-actions { flex-direction: column; }
  .success-actions :deep(.el-button) { width: 100%; }
  .next-quest { align-items: flex-start; }
  .next-quest :deep(.el-button) { padding: 6px 0; }
  .next-quest span { white-space: normal; }
}
</style>
