<template>
  <div class="dashboard merchant-dashboard">
    <section class="dashboard-hero" aria-labelledby="merchant-dashboard-title">
      <span class="hero-orbit hero-orbit-one" aria-hidden="true"></span>
      <span class="hero-orbit hero-orbit-two" aria-hidden="true"></span>
      <span class="hero-sparkle sparkle-one" aria-hidden="true">✦</span>
      <span class="hero-sparkle sparkle-two" aria-hidden="true">✦</span>

      <div class="hero-copy">
        <div class="eyebrow"><span class="eyebrow-dot">✦</span> 商家中心 · 今日营业中</div>
        <h2 id="merchant-dashboard-title">欢迎回来，<span>店长！</span></h2>
        <p>把灵感变成好物，让每一次上架都更有底气。</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" class="hero-primary-action" @click="startProduct">
            <span aria-hidden="true">＋</span> 创建新商品
          </el-button>
          <el-button size="large" class="hero-secondary-action" @click="openMyStore">
            <span aria-hidden="true">↗</span> 预览我的店铺
          </el-button>
        </div>
      </div>

      <div class="hero-mascot" aria-hidden="true">
        <div class="mascot-glow"></div>
        <JmallMascot variant="wave" :size="146" :animated="true" />
        <span class="mascot-caption">今天也要闪闪发光</span>
      </div>

      <div class="hero-level" aria-label="店铺成长进度">
        <div class="level-heading">
          <span>店铺成长</span>
          <strong>Lv. {{ merchantLevel }}</strong>
        </div>
        <div class="level-track" role="progressbar" :aria-valuenow="levelProgress" aria-valuemin="0" aria-valuemax="100">
          <span :style="{ width: `${levelProgress}%` }"></span>
        </div>
        <small>再上架 {{ productsUntilNextLevel }} 件商品升级</small>
      </div>
    </section>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-row :gutter="20" class="loading-stats">
        <el-col :span="8"><el-skeleton animated><template #template><el-skeleton-item variant="rect" class="skeleton-card" /></template></el-skeleton></el-col>
        <el-col :span="8"><el-skeleton animated><template #template><el-skeleton-item variant="rect" class="skeleton-card" /></template></el-skeleton></el-col>
        <el-col :span="8"><el-skeleton animated><template #template><el-skeleton-item variant="rect" class="skeleton-card" /></template></el-skeleton></el-col>
      </el-row>
      <el-skeleton :rows="5" animated class="skeleton-content" />
    </div>

    <!-- Error State -->
    <el-result v-else-if="error" icon="error" title="加载失败" :sub-title="error">
      <template #extra>
        <el-button type="primary" @click="loadDashboard">🔄 重新加载</el-button>
      </template>
    </el-result>

    <template v-else>
      <section class="stats-grid" aria-label="店铺经营数据">
        <el-card
          shadow="never"
          class="stat-card stat-card-link stat-card-products"
          role="button"
          tabindex="0"
          aria-label="进入我的店铺查看已上架商品"
          @click="openMyStore"
          @keyup.enter="openMyStore"
        >
          <div class="stat-card-top"><span class="stat-icon">🛍️</span><span class="stat-bubble">店铺</span></div>
          <div class="stat-value">{{ stats.productCount }}</div>
          <div class="stat-label">已上架商品</div>
          <div class="stat-hint">点击进入我的店铺 <span aria-hidden="true">→</span></div>
        </el-card>
        <el-card shadow="never" class="stat-card stat-card-sales">
          <div class="stat-card-top"><span class="stat-icon">🪙</span><span class="stat-bubble">人气</span></div>
          <div class="stat-value">{{ formatViews(stats.totalSales) }}</div>
          <div class="stat-label">累计售出</div>
          <div class="stat-hint">每一件好物都值得被看见</div>
        </el-card>
        <el-card shadow="never" class="stat-card stat-card-orders">
          <div class="stat-card-top"><span class="stat-icon">📦</span><span class="stat-bubble">订单</span></div>
          <div class="stat-value">{{ formatViews(stats.totalOrders) }}</div>
          <div class="stat-label">累计订单</div>
          <div class="stat-hint">稳稳接住每一份喜欢</div>
        </el-card>
      </section>

      <section class="dashboard-grid">
        <el-card shadow="never" class="journey-card">
          <template #header>
            <div class="section-heading">
              <div>
                <span class="section-kicker">SHOP QUEST</span>
                <h3>今天的经营旅程</h3>
              </div>
              <span class="section-pill">轻松 3 步</span>
            </div>
          </template>
          <div class="journey-list">
            <div class="journey-step journey-step-active">
              <div class="step-number">1</div>
              <div class="step-copy"><strong>把商品说清楚</strong><span>完整的信息，让 AI 更懂你的好物</span></div>
              <el-button text type="primary" @click="startProduct">去填写 <span aria-hidden="true">→</span></el-button>
            </div>
            <div class="journey-step">
              <div class="step-number">2</div>
              <div class="step-copy"><strong>让 AI 变漂亮</strong><span>生成一个平台专属的商品主稿</span></div>
              <span class="step-state">待解锁</span>
            </div>
            <div class="journey-step">
              <div class="step-number">3</div>
              <div class="step-copy"><strong>让顾客看见</strong><span>发布后还能随时编辑和优化</span></div>
              <span class="step-state">待解锁</span>
            </div>
          </div>
        </el-card>

        <el-card shadow="never" class="ai-card">
          <div class="ai-card-art">
            <div class="ai-burst" aria-hidden="true">✦</div>
            <JmallMascot variant="idle" :size="102" :animated="true" label="Jmall AI 店员" />
          </div>
          <div class="ai-card-copy">
            <span class="section-kicker">AI SHOP ASSISTANT</span>
            <h3>让小店更有自己的味道</h3>
            <p>从市场观察到平台文案，AI 店员会陪你把每件商品打磨得更完整。</p>
            <div class="ai-feature-list">
              <span><i>✦</i> 生成平台专属文案</span>
              <span><i>✦</i> 联网观察行业趋势</span>
              <span><i>✦</i> 上架前自动合规检查</span>
            </div>
            <el-button text type="primary" class="ai-link" @click="startProduct">进入商品工作室 <span aria-hidden="true">↗</span></el-button>
          </div>
        </el-card>
      </section>

      <section class="tip-strip" aria-label="经营小贴士">
        <div class="tip-mascot"><JmallMascot variant="mark" :size="46" :animated="false" /></div>
        <div><strong>店长小贴士</strong><span>商品信息越完整，AI 越能写出贴近你心意的内容。</span></div>
        <el-button text @click="startProduct">开始完善 <span aria-hidden="true">→</span></el-button>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { storeApi } from '@/services/stores'
import JmallMascot from '@/components/brand/JmallMascot.vue'

const router = useRouter()
const loading = ref(true)
const error = ref<string | null>(null)

const stats = ref({
  storeId: 0,
  productCount: 0,
  totalSales: 0,
  totalOrders: 0,
})

const merchantLevel = computed(() => Math.max(1, Math.floor(stats.value.productCount / 3) + 1))
const levelProgress = computed(() => Math.round((stats.value.productCount % 3) / 3 * 100))
const productsUntilNextLevel = computed(() => 3 - (stats.value.productCount % 3))

function formatViews(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

function startProduct() {
  router.push('/merchant/products/new')
}

function openMyStore() {
  if (!stats.value.storeId) {
    ElMessage.warning('当前账号还没有可预览的店铺')
    return
  }
  router.push(`/store/${stats.value.storeId}`)
}

onMounted(() => { loadDashboard() })

async function loadDashboard() {
  loading.value = true
  error.value = null
  try {
    const result = await storeApi.getMyStats()
    stats.value.storeId = Number(result.storeId || 0)
    stats.value.productCount = result.productCount || 0
    stats.value.totalSales = result.totalSales || 0
    stats.value.totalOrders = result.totalOrders || 0
  } catch (e: any) {
    error.value = e.message || '工作台数据加载失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dashboard {
  --merchant-ink: #312b45;
  --merchant-muted: #8d879e;
  --merchant-pink: #f25d78;
  --merchant-pink-dark: #dc4967;
  --merchant-lavender: #7563c9;
  --merchant-mint: #6dcfaf;
  --merchant-yellow: #ffd76b;
  max-width: 1180px;
  margin: 0 auto;
  padding: 26px 28px 48px;
}

.dashboard-hero {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 190px 210px;
  align-items: center;
  min-height: 260px;
  overflow: hidden;
  padding: 32px 38px 30px 42px;
  border: 1px solid rgba(255, 255, 255, .7);
  border-radius: 30px;
  background: linear-gradient(120deg, #fff0f1 0%, #f8ecfb 54%, #eee9ff 100%);
  box-shadow: 0 18px 46px rgba(104, 84, 140, .12);
}
.hero-orbit { position: absolute; border: 1px solid rgba(157, 114, 189, .15); border-radius: 50%; pointer-events: none; }
.hero-orbit-one { width: 380px; height: 380px; right: 100px; top: -190px; }
.hero-orbit-two { width: 210px; height: 210px; right: 18px; bottom: -120px; border-color: rgba(242, 93, 120, .16); }
.hero-sparkle { position: absolute; color: var(--merchant-yellow); font-size: 25px; pointer-events: none; }
.sparkle-one { top: 26px; right: 294px; transform: rotate(15deg); }
.sparkle-two { right: 30px; bottom: 70px; color: var(--merchant-mint); font-size: 17px; }
.hero-copy { position: relative; z-index: 1; min-width: 0; }
.eyebrow, .section-kicker { color: var(--merchant-pink-dark); font-size: 11px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
.eyebrow { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.eyebrow-dot { color: var(--merchant-yellow); font-size: 16px; }
.hero-copy h2 { margin: 0; color: var(--merchant-ink); font-size: clamp(28px, 4vw, 40px); font-weight: 850; letter-spacing: -.045em; line-height: 1.15; }
.hero-copy h2 span { color: var(--merchant-pink); }
.hero-copy p { max-width: 440px; margin: 12px 0 22px; color: #756f88; font-size: 15px; line-height: 1.7; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.hero-actions :deep(.el-button) { height: 42px; margin: 0; border-radius: 14px; font-weight: 700; }
.hero-primary-action { border: none; background: var(--merchant-pink); box-shadow: 0 9px 18px rgba(242, 93, 120, .23); }
.hero-primary-action:hover { border-color: var(--merchant-pink-dark); background: var(--merchant-pink-dark); }
.hero-secondary-action { border: 1px solid rgba(117, 99, 201, .18); color: var(--merchant-lavender); background: rgba(255, 255, 255, .62); }
.hero-secondary-action:hover { color: var(--merchant-lavender); border-color: rgba(117, 99, 201, .35); background: #fff; }
.hero-mascot { position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 190px; }
.mascot-glow { position: absolute; width: 146px; height: 100px; border-radius: 50%; background: rgba(242, 93, 120, .15); filter: blur(15px); transform: translateY(18px); }
.hero-mascot :deep(.jmall-mascot) { position: relative; }
.mascot-caption { margin-top: -5px; padding: 5px 12px; border-radius: 99px; color: #a95774; background: rgba(255,255,255,.65); font-size: 11px; font-weight: 700; }
.hero-level { position: relative; z-index: 1; align-self: end; padding: 16px 17px; border: 1px solid rgba(255, 255, 255, .78); border-radius: 18px; background: rgba(255, 255, 255, .62); backdrop-filter: blur(8px); }
.level-heading { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; color: #756f88; font-size: 12px; font-weight: 700; }
.level-heading strong { color: var(--merchant-lavender); font-size: 15px; }
.level-track { height: 8px; overflow: hidden; border-radius: 10px; background: #e8e3f2; }
.level-track span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--merchant-pink), #ac80db); transition: width .35s ease; }
.hero-level small { display: block; margin-top: 9px; color: #9a91ab; font-size: 11px; line-height: 1.4; }

.loading-state { padding-top: 22px; }
.loading-stats { margin: 0; }
.skeleton-card { width: 100%; height: 148px; border-radius: 22px; }
.skeleton-content { max-width: 100%; margin-top: 22px; padding: 22px; border-radius: 22px; background: #fff; }

.stats-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; margin-top: 22px; }
.stat-card { min-height: 172px; overflow: hidden; border: 1px solid #f0ecf5; border-radius: 22px; background: #fff; box-shadow: 0 9px 25px rgba(73, 56, 93, .06); transition: transform .2s ease, box-shadow .2s ease; }
.stat-card :deep(.el-card__body) { height: 100%; padding: 21px 23px 19px; }
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 15px 31px rgba(73, 56, 93, .1); }
.stat-card-link { cursor: pointer; }
.stat-card-link:focus-visible { outline: 3px solid rgba(242, 93, 120, .26); outline-offset: 3px; }
.stat-card-products { background: linear-gradient(135deg, #fff 0%, #fff4f3 100%); }
.stat-card-sales { background: linear-gradient(135deg, #fff 0%, #fff9e8 100%); }
.stat-card-orders { background: linear-gradient(135deg, #fff 0%, #f1f8f5 100%); }
.stat-card-top { display: flex; align-items: center; justify-content: space-between; }
.stat-icon { display: grid; width: 43px; height: 43px; place-items: center; border-radius: 14px; background: rgba(255,255,255,.8); font-size: 24px; box-shadow: 0 5px 13px rgba(103, 78, 108, .08); }
.stat-bubble { padding: 5px 9px; border-radius: 99px; color: #a39aac; background: rgba(255,255,255,.76); font-size: 11px; font-weight: 700; }
.stat-value { margin-top: 12px; color: var(--merchant-ink); font-size: 29px; font-weight: 850; letter-spacing: -.04em; }
.stat-label { margin-top: 1px; color: #766f83; font-size: 13px; font-weight: 700; }
.stat-hint { margin-top: 8px; color: #a19aaa; font-size: 11px; line-height: 1.4; }
.stat-card-products .stat-hint { color: var(--merchant-pink); }

.dashboard-grid { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(330px, .95fr); gap: 18px; margin-top: 18px; }
.journey-card, .ai-card { min-height: 320px; border: 1px solid #f0ecf5; border-radius: 22px; background: #fff; box-shadow: 0 9px 25px rgba(73, 56, 93, .05); }
.journey-card :deep(.el-card__header) { padding: 21px 24px 16px; border-bottom: 1px solid #f4f1f6; }
.journey-card :deep(.el-card__body) { padding: 8px 24px 20px; }
.section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.section-heading h3 { margin: 5px 0 0; color: var(--merchant-ink); font-size: 18px; font-weight: 800; }
.section-pill { padding: 6px 10px; border-radius: 99px; color: #8e65ad; background: #f6eafa; font-size: 11px; font-weight: 700; white-space: nowrap; }
.journey-list { display: flex; flex-direction: column; }
.journey-step { display: flex; align-items: center; gap: 13px; min-height: 75px; border-bottom: 1px dashed #eeeaf2; }
.journey-step:last-child { border-bottom: none; }
.journey-step-active { margin: 0 -10px; padding: 0 10px; border-radius: 14px; background: #fff8f6; }
.step-number { display: grid; width: 30px; height: 30px; flex: 0 0 auto; place-items: center; border: 1px solid #e8e0f5; border-radius: 50%; color: #9174c3; background: #faf8ff; font-size: 13px; font-weight: 800; }
.journey-step-active .step-number { border-color: #f7b1ba; color: #fff; background: var(--merchant-pink); box-shadow: 0 4px 10px rgba(242, 93, 120, .2); }
.step-copy { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 4px; }
.step-copy strong { color: #484157; font-size: 13px; }
.step-copy span { overflow: hidden; color: #9b94a6; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.journey-step :deep(.el-button) { flex: 0 0 auto; padding: 5px 0; font-size: 12px; }
.step-state { flex: 0 0 auto; color: #b1aabb; font-size: 11px; }
.ai-card { display: flex; align-items: center; gap: 12px; overflow: hidden; padding: 22px 23px; background: linear-gradient(135deg, #f5f1ff 0%, #fff6f5 100%); }
.ai-card-art { position: relative; display: flex; width: 122px; flex: 0 0 auto; align-self: stretch; align-items: center; justify-content: center; }
.ai-card-art::before { position: absolute; width: 112px; height: 112px; border-radius: 45% 55% 50% 50%; background: rgba(255,255,255,.72); content: ''; transform: rotate(-10deg); }
.ai-card-art :deep(.jmall-mascot) { z-index: 1; }
.ai-burst { position: absolute; z-index: 2; top: 12px; right: 1px; color: var(--merchant-yellow); font-size: 22px; animation: twinkle 2s ease-in-out infinite; }
.ai-card-copy { min-width: 0; }
.ai-card-copy h3 { margin: 5px 0 8px; color: var(--merchant-ink); font-size: 18px; font-weight: 800; line-height: 1.35; }
.ai-card-copy p { margin: 0; color: #7f788d; font-size: 12px; line-height: 1.65; }
.ai-feature-list { display: flex; flex-direction: column; gap: 5px; margin-top: 13px; }
.ai-feature-list span { color: #756b83; font-size: 11px; }
.ai-feature-list i { margin-right: 5px; color: var(--merchant-pink); font-style: normal; }
.ai-link { margin-top: 11px; padding: 0; font-size: 12px; font-weight: 800; }

.tip-strip { display: flex; align-items: center; gap: 13px; margin-top: 18px; padding: 13px 16px; border: 1px solid #f3e9c7; border-radius: 18px; background: linear-gradient(90deg, #fffaf0, #fffdf7); }
.tip-mascot { display: grid; width: 48px; height: 48px; flex: 0 0 auto; place-items: center; border-radius: 15px; background: #fff2d4; }
.tip-strip > div:nth-child(2) { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 3px; }
.tip-strip strong { color: #6f5a36; font-size: 12px; }
.tip-strip span { overflow: hidden; color: #9a8764; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.tip-strip :deep(.el-button) { color: #b27a27; font-size: 12px; font-weight: 800; }

@keyframes twinkle { 0%, 100% { opacity: .45; transform: scale(.9) rotate(0); } 50% { opacity: 1; transform: scale(1.1) rotate(18deg); } }

@media (prefers-reduced-motion: reduce) { .stat-card, .ai-burst { transition: none; animation: none; } }
@media (max-width: 900px) {
  .dashboard-hero { grid-template-columns: minmax(0, 1fr) 150px; padding-left: 28px; }
  .hero-level { grid-column: 1 / -1; align-self: auto; margin-top: 10px; }
  .hero-mascot { grid-column: 2; grid-row: 1; }
  .hero-orbit-one { right: -70px; }
  .dashboard-grid { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .dashboard { padding: 16px 14px 34px; }
  .dashboard-hero { display: block; min-height: 0; padding: 24px 22px 20px; }
  .hero-copy { padding-right: 4px; }
  .hero-copy h2 { font-size: 30px; }
  .hero-mascot { position: absolute; top: 14px; right: -4px; transform: scale(.72); transform-origin: top right; }
  .mascot-caption { display: none; }
  .hero-level { margin-top: 18px; }
  .stats-grid { grid-template-columns: 1fr; gap: 12px; }
  .stat-card { min-height: 142px; }
  .ai-card { align-items: flex-start; padding: 18px 16px; }
  .ai-card-art { width: 88px; }
  .ai-card-art::before { width: 84px; height: 84px; }
  .ai-card-art :deep(.jmall-mascot) { transform: scale(.8); }
  .tip-strip { align-items: flex-start; }
  .tip-strip span { white-space: normal; }
  .tip-strip :deep(.el-button) { padding: 5px 0; }
}
</style>
