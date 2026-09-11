<template>
  <div id="jmall-app" :class="[`theme-${currentTheme}`]">
    <header class="jmall-topbar">
      <button class="brand-button" type="button" aria-label="返回 Jmall 首页" @click="goHome">
        <img class="brand-lockup" :src="logoLockup" alt="Jmall" />
        <img class="brand-mark" :src="logoMark" alt="" aria-hidden="true" />
        <span>AI 电商模拟经营平台</span>
      </button>

      <nav class="mode-switch" aria-label="主要功能">
        <button type="button" :class="{ active: !isMerchantMode }" @click="$router.push('/shop')">
          <el-icon><ShoppingBag /></el-icon><span>逛逛好物</span>
        </button>
        <button type="button" :class="{ active: isMerchantMode }" @click="goMerchant">
          <el-icon><MagicStick /></el-icon><span>经营小店</span>
        </button>
      </nav>

      <div class="topbar-right">
        <div v-if="authStore.isAuthenticated" class="level-chip" title="根据当前金币展示成长进度">
          <span class="level-badge">Lv.{{ growthLevel }}</span>
          <span class="level-label">{{ growthTitle }}</span>
          <span class="level-track" aria-hidden="true"><i :style="{ width: `${growthProgress}%` }"></i></span>
        </div>

        <button
          v-if="authStore.isAuthenticated && !isMerchantMode"
          class="icon-button cart-entry"
          type="button"
          aria-label="查看购物车"
          @click="$router.push('/shop/cart')"
        >
          <el-badge :value="cartCount" :hidden="cartCount === 0" :max="99">
            <el-icon :size="21"><ShoppingCart /></el-icon>
          </el-badge>
        </button>

        <div v-if="authStore.isAuthenticated" class="gold-display">
          <span class="coin-token">●</span>
          <span class="gold-amount">{{ formatNumber(authStore.goldBalance) }}</span>
          <button type="button" :disabled="checkedInToday" @click="doCheckin">
            {{ checkedInToday ? '已签到' : '签到' }}
          </button>
        </div>

        <template v-if="authStore.isAuthenticated">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="34" :src="logoMark" />
              <span class="username">{{ authStore.displayName }}</span>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile"><el-icon><User /></el-icon>个人中心</el-dropdown-item>
                <el-dropdown-item command="orders"><el-icon><Document /></el-icon>我的订单</el-dropdown-item>
                <el-dropdown-item command="collections"><el-icon><Star /></el-icon>我的收藏</el-dropdown-item>
                <el-dropdown-item command="cart">
                  <el-icon><ShoppingCart /></el-icon>购物车
                  <el-badge :value="cartCount" :hidden="cartCount === 0" class="menu-badge" />
                </el-dropdown-item>
                <el-dropdown-item divided command="merchant"><el-icon><Shop /></el-icon>商家中心</el-dropdown-item>
                <el-dropdown-item command="leaderboard"><el-icon><Trophy /></el-icon>排行榜</el-dropdown-item>
                <el-dropdown-item command="achievements"><el-icon><Medal /></el-icon>成就</el-dropdown-item>
                <el-dropdown-item divided command="logout"><el-icon><SwitchButton /></el-icon>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button class="login-button" type="primary" @click="$router.push('/login')">登录</el-button>
          <el-button class="register-button" @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </header>

    <main class="jmall-main">
      <router-view v-slot="{ Component }">
        <transition name="page-pop" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <AchievementPopup v-if="latestAchievement" :achievement="latestAchievement" @close="latestAchievement = null" />
    <PurchaseEffect ref="purchaseEffectRef" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, provide, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGamificationStore } from '@/stores/gamification'
import http from '@/services/http'
import AchievementPopup from '@/components/game/AchievementPopup.vue'
import PurchaseEffect from '@/components/game/PurchaseEffect.vue'
import logoLockup from '@/assets/v0.3/brand/jmall-logo-lockup.svg'
import logoMark from '@/assets/v0.3/brand/jmall-logo-mark.svg'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const gamificationStore = useGamificationStore()

const currentTheme = ref('playful')
const checkedInToday = computed(() => gamificationStore.checkedInToday)
const isMerchantMode = computed(() => route.path.startsWith('/merchant'))
const growthLevel = computed(() => Math.floor(authStore.goldBalance / 1000) + 1)
const growthProgress = computed(() => Math.round((authStore.goldBalance % 1000) / 10))
const growthTitle = computed(() => growthLevel.value >= 10 ? '好物达人' : growthLevel.value >= 5 ? '经营能手' : '新手掌柜')
const latestAchievement = ref<any>(null)
const purchaseEffectRef = ref()
const cartCount = ref(0)

provide('triggerPurchaseEffect', (product: any, multiplier: number, goldEarned: number) => {
  purchaseEffectRef.value?.play(product, multiplier, goldEarned)
})
provide('showAchievement', (achievement: any) => {
  latestAchievement.value = achievement
  setTimeout(() => { latestAchievement.value = null }, 4000)
})
provide('refreshCartCount', fetchCartCount)

async function fetchCartCount() {
  if (!authStore.isAuthenticated) return
  try {
    const items = await http.get('/cart')
    cartCount.value = Array.isArray(items) ? items.length : 0
  } catch {
    cartCount.value = 0
  }
}

function goHome() { router.push('/shop') }

function goMerchant() {
  if (authStore.isAuthenticated) {
    router.push('/merchant')
    return
  }
  router.push({ path: '/login', query: { redirect: '/merchant' } })
}

function doCheckin() {
  const beforeKeys = new Set(gamificationStore.achievements.filter(a => a.unlocked).map(a => a.key))
  gamificationStore.checkin().then((result) => {
    authStore.addGold(result.goldReward)
    const afterUnlocked = gamificationStore.achievements.filter(a => a.unlocked)
    const newAchievement = afterUnlocked.find(a => !beforeKeys.has(a.key))
    if (newAchievement) {
      latestAchievement.value = newAchievement
      setTimeout(() => { latestAchievement.value = null }, 4000)
    }
  })
}

function handleUserCommand(command: string) {
  switch (command) {
    case 'profile': router.push('/profile'); break
    case 'orders': router.push('/shop/orders'); break
    case 'collections': router.push('/collections'); break
    case 'cart': router.push('/shop/cart'); break
    case 'merchant': router.push('/merchant'); break
    case 'leaderboard': router.push('/leaderboard'); break
    case 'achievements': router.push('/achievements'); break
    case 'logout': authStore.logout(); router.push('/login'); break
  }
}

function formatNumber(n: number): string {
  if (n >= 100000000) return `${(n / 100000000).toFixed(1)}亿`
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return n.toLocaleString()
}

watch(() => authStore.currentUser?.id, (userId) => {
  if (userId) {
    fetchCartCount()
    gamificationStore.checkTodayStatus()
  }
})

onMounted(() => {
  if (authStore.isAuthenticated) {
    fetchCartCount()
    gamificationStore.checkTodayStatus()
  }
})
</script>

<style scoped>
.jmall-topbar {
  position: sticky; top: 0; z-index: 1000;
  display: grid; grid-template-columns: minmax(220px, 1fr) auto minmax(330px, 1fr); align-items: center;
  min-height: 72px; padding: 8px clamp(16px, 3vw, 44px);
  border-bottom: 1px solid rgba(238, 223, 210, .85); background: rgba(255, 254, 253, .92);
  box-shadow: 0 7px 28px rgba(82, 55, 79, .07); backdrop-filter: blur(18px);
}
.brand-button { display: flex; align-items: center; width: max-content; min-width: 0; border: 0; color: var(--jm-muted); background: none; cursor: pointer; }
.brand-lockup { width: 126px; height: 46px; object-fit: contain; object-position: left center; }
.brand-mark { display: none; }
.brand-button span { padding-left: 8px; border-left: 1px solid var(--jm-line); font-size: 12px; white-space: nowrap; }
.mode-switch { display: flex; gap: 5px; padding: 5px; border: 1px solid var(--jm-line); border-radius: 16px; background: var(--jm-soft); }
.mode-switch button { display: flex; align-items: center; gap: 6px; min-height: 38px; padding: 0 17px; border: 0; border-radius: 11px; color: var(--jm-muted); background: transparent; font: inherit; font-size: 13px; font-weight: 700; cursor: pointer; transition: .2s ease; }
.mode-switch button:hover { color: var(--jm-red); }
.mode-switch button.active { color: var(--jm-red); background: #fff; box-shadow: 0 4px 14px rgba(103, 69, 91, .09); }
.topbar-right { display: flex; align-items: center; justify-content: flex-end; gap: 10px; min-width: 0; }
.level-chip { display: grid; grid-template-columns: auto auto; align-items: center; gap: 2px 6px; min-width: 122px; }
.level-badge { color: var(--jm-red); font-size: 12px; font-weight: 800; }
.level-label { overflow: hidden; color: var(--jm-muted); font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.level-track { grid-column: 1 / -1; overflow: hidden; height: 5px; border-radius: 99px; background: var(--jm-soft); }
.level-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--jm-yellow), var(--jm-red)); }
.icon-button { display: grid; width: 38px; height: 38px; place-items: center; border: 0; border-radius: 12px; color: var(--jm-text); background: transparent; cursor: pointer; }
.icon-button:hover { background: var(--jm-soft); transform: translateY(-1px); }
.gold-display { display: flex; align-items: center; gap: 6px; min-height: 40px; padding: 4px 5px 4px 10px; border: 1px solid #f3d58d; border-radius: 14px; background: #fff9e9; }
.coin-token { display: grid; width: 17px; height: 17px; place-items: center; border: 2px solid #e7a928; border-radius: 50%; color: #f7c448; font-size: 8px; }
.gold-amount { min-width: 40px; color: #bd7b14; font-size: 13px; font-weight: 800; }
.gold-display button { min-height: 29px; padding: 0 9px; border: 0; border-radius: 9px; color: #a5660c; background: #ffeab6; font: inherit; font-size: 11px; font-weight: 700; cursor: pointer; }
.gold-display button:disabled { color: #bda979; background: #fff2d4; cursor: default; }
.user-info { display: flex; align-items: center; gap: 7px; min-height: 42px; padding: 3px 8px 3px 4px; border: 1px solid transparent; border-radius: 16px; cursor: pointer; }
.user-info:hover { border-color: var(--jm-line); background: var(--jm-soft); }
.username { max-width: 84px; overflow: hidden; color: var(--jm-text); font-size: 13px; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.dropdown-arrow { color: var(--jm-muted); font-size: 11px; }
.menu-badge { margin-left: 4px; }
.login-button, .register-button { border-radius: 12px; font-weight: 700; }
.jmall-main { flex: 1; min-width: 0; }

@media (max-width: 1100px) {
  .jmall-topbar { grid-template-columns: minmax(155px, 1fr) auto minmax(250px, 1fr); }
  .brand-button span, .level-chip { display: none; }
  .brand-lockup { width: 112px; }
}
@media (max-width: 760px) {
  .jmall-topbar { grid-template-columns: auto 1fr auto; min-height: 62px; padding: 7px 12px; }
  .brand-lockup { width: 88px; height: 40px; }
  .mode-switch { justify-self: center; padding: 4px; }
  .mode-switch button { min-height: 34px; padding: 0 10px; }
  .mode-switch button span, .username, .cart-entry, .gold-amount { display: none; }
  .gold-display { min-height: 36px; padding-left: 7px; }
  .gold-display button { padding: 0 7px; }
  .user-info { padding-right: 4px; }
}
@media (max-width: 480px) {
  .brand-lockup { display: none; }
  .brand-mark { display: block; width: 40px; height: 40px; object-fit: contain; }
  .gold-display { display: none; }
  .topbar-right { gap: 3px; }
}
</style>
