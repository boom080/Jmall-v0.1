<template>
  <div class="merchant-layout">
    <aside class="merchant-sidebar">
      <section class="store-card">
        <JmallMascot variant="wave" :size="62" />
        <div>
          <span>欢迎回来，掌柜</span>
          <strong>{{ authStore.displayName }}的小店</strong>
        </div>
      </section>

      <el-menu :default-active="activeMenu" router class="merchant-menu">
        <el-menu-item index="/merchant">
          <el-icon><DataAnalysis /></el-icon><span>经营总览</span>
        </el-menu-item>
        <el-menu-item index="/merchant/products">
          <el-icon><Goods /></el-icon><span>我的商品</span>
        </el-menu-item>
        <el-menu-item index="/merchant/products/new" class="ai-menu-item">
          <el-icon><MagicStick /></el-icon><span>AI 商品工作室</span><i>推荐</i>
        </el-menu-item>
        <el-menu-item index="/merchant/knowledge">
          <el-icon><Document /></el-icon><span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/achievements">
          <el-icon><Medal /></el-icon><span>成长成就</span>
        </el-menu-item>
      </el-menu>

      <section class="daily-tip">
        <span class="tip-kicker">今日经营建议</span>
        <strong>完善或上架一件好物</strong>
        <p>把信息写完整，AI 才能更懂你的商品。</p>
        <button type="button" @click="router.push('/merchant/products/new')">去完成 <span>→</span></button>
      </section>
    </aside>

    <main class="merchant-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in"><component :is="Component" /></transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import JmallMascot from '@/components/brand/JmallMascot.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const path = route.path
  if (path === '/merchant/products/new') return '/merchant/products/new'
  if (path.startsWith('/merchant/products')) return '/merchant/products'
  if (path.startsWith('/merchant/knowledge')) return '/merchant/knowledge'
  return '/merchant'
})
</script>

<style scoped>
.merchant-layout { display: grid; grid-template-columns: 244px minmax(0, 1fr); min-height: calc(100vh - 72px); }
.merchant-sidebar { position: sticky; top: 72px; display: flex; height: calc(100vh - 72px); flex-direction: column; padding: 18px 14px; border-right: 1px solid var(--jm-line); background: rgba(255, 254, 253, .88); backdrop-filter: blur(12px); }
.store-card { display: flex; align-items: center; gap: 8px; min-height: 82px; padding: 8px 9px; margin-bottom: 12px; border: 1px solid #f3ded8; border-radius: 18px; background: linear-gradient(135deg, #fff8ee, #ffeef1); }
.store-card > div { display: grid; min-width: 0; gap: 3px; }
.store-card span { color: var(--jm-muted); font-size: 11px; }
.store-card strong { overflow: hidden; color: var(--jm-text); font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.merchant-menu { flex: 0 0 auto; border-right: 0; background: transparent; }
.merchant-menu :deep(.el-menu-item) { position: relative; height: 46px; margin: 3px 0; border-radius: 13px; color: var(--jm-muted); font-weight: 700; }
.merchant-menu :deep(.el-menu-item:hover) { color: var(--jm-red); background: var(--jm-soft); }
.merchant-menu :deep(.el-menu-item.is-active) { color: var(--jm-red); background: var(--jm-pink-soft); }
.merchant-menu :deep(.el-menu-item.is-active::before) { position: absolute; left: 0; width: 4px; height: 22px; border-radius: 0 4px 4px 0; background: var(--jm-red); content: ''; }
.ai-menu-item i { position: absolute; right: 10px; padding: 2px 6px; border-radius: 99px; color: #a96600; background: var(--jm-yellow-soft); font-size: 9px; font-style: normal; }
.daily-tip { margin-top: auto; padding: 16px; border: 1px solid #eadff9; border-radius: 18px; background: linear-gradient(145deg, #f5f1ff, #fff6eb); box-shadow: var(--jm-shadow-soft); }
.tip-kicker { color: var(--jm-purple); font-size: 10px; font-weight: 800; letter-spacing: .08em; }
.daily-tip strong { display: block; margin-top: 5px; font-size: 13px; }
.daily-tip p { margin: 7px 0 12px; color: var(--jm-muted); font-size: 11px; line-height: 1.55; }
.daily-tip button { width: 100%; min-height: 34px; border: 0; border-radius: 10px; color: #fff; background: var(--jm-purple); font-size: 11px; font-weight: 700; cursor: pointer; }
.daily-tip button span { margin-left: 4px; }
.merchant-content { min-width: 0; padding: clamp(18px, 3vw, 34px); overflow: auto; }

@media (max-width: 900px) {
  .merchant-layout { grid-template-columns: 82px minmax(0, 1fr); }
  .merchant-sidebar { padding: 12px 9px; }
  .store-card { justify-content: center; padding: 6px; }
  .store-card > div, .daily-tip { display: none; }
  .merchant-menu :deep(.el-menu-item) { justify-content: center; padding: 0 !important; }
  .merchant-menu :deep(.el-menu-item span), .ai-menu-item i { display: none; }
  .merchant-menu :deep(.el-icon) { margin: 0; font-size: 20px; }
}

@media (max-width: 680px) {
  .merchant-layout { display: block; min-height: calc(100vh - 62px); padding-bottom: 68px; }
  .merchant-sidebar { position: fixed; z-index: 900; top: auto; right: 0; bottom: 0; left: 0; display: block; width: auto; height: 64px; padding: 6px 7px max(6px, env(safe-area-inset-bottom)); border-top: 1px solid var(--jm-line); border-right: 0; background: rgba(255, 254, 253, .96); }
  .store-card, .daily-tip { display: none; }
  .merchant-menu { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); }
  .merchant-menu :deep(.el-menu-item) { display: grid; height: 51px; place-content: center; gap: 0; margin: 0; font-size: 9px; line-height: 1; }
  .merchant-menu :deep(.el-menu-item span) { display: block; margin-top: 2px; font-size: 9px; }
  .merchant-menu :deep(.el-icon) { margin: auto; font-size: 18px; }
  .merchant-menu :deep(.el-menu-item.is-active::before) { top: -6px; left: 50%; width: 23px; height: 3px; border-radius: 0 0 4px 4px; transform: translateX(-50%); }
  .ai-menu-item i { display: none; }
  .merchant-content { padding: 14px 12px; }
}
</style>
