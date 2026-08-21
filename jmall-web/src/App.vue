<template>
  <div id="jmall-app" :class="[`theme-${currentTheme}`]">
    <!-- Top Navigation Bar -->
    <header class="jmall-topbar">
      <div class="topbar-left">
        <h1 class="app-logo" @click="goHome">🛍️ Jmall</h1>
        <span class="app-subtitle">AI 电商模拟经营平台</span>
      </div>

      <div class="topbar-right">
        <!-- Cart Icon with Badge -->
        <div class="cart-entry" @click="$router.push('/shop/cart')" v-if="authStore.isAuthenticated">
          <el-badge :value="cartCount" :hidden="cartCount === 0" :max="99">
            <el-icon :size="24"><ShoppingCart /></el-icon>
          </el-badge>
        </div>

        <!-- Gold Display -->
        <div class="gold-display" v-if="authStore.isAuthenticated">
          <el-icon><Coin /></el-icon>
          <span class="gold-amount">{{ formatNumber(authStore.goldBalance) }}</span>
          <el-button size="small" type="warning" plain @click="doCheckin" :disabled="checkedInToday">
            {{ checkedInToday ? '已签到' : '📅 签到' }}
          </el-button>
        </div>

        <!-- User Menu -->
        <template v-if="authStore.isAuthenticated">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="32" icon="UserFilled" />
              <span class="username">{{ authStore.displayName }}</span>
              <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon> 个人中心
                </el-dropdown-item>
                <el-dropdown-item command="orders">
                  <el-icon><Document /></el-icon> 我的订单
                </el-dropdown-item>
                <el-dropdown-item command="collections">
                  <el-icon><Star /></el-icon> 我的收藏
                </el-dropdown-item>
                <el-dropdown-item command="cart">
                  <el-icon><ShoppingCart /></el-icon> 购物车
                  <el-badge :value="cartCount" :hidden="cartCount === 0" style="margin-left: 4px" />
                </el-dropdown-item>
                <el-dropdown-item divided command="merchant">
                  <el-icon><Shop /></el-icon> 商家中心
                </el-dropdown-item>
                <el-dropdown-item command="leaderboard">
                  <el-icon><Trophy /></el-icon> 排行榜
                </el-dropdown-item>
                <el-dropdown-item command="achievements">
                  <el-icon><Medal /></el-icon> 成就
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon> 退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>
        <template v-else>
          <el-button type="primary" size="small" @click="$router.push('/login')">登录</el-button>
          <el-button size="small" @click="$router.push('/register')">注册</el-button>
        </template>
      </div>
    </header>

    <!-- Main Content -->
    <main class="jmall-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Achievement Popup -->
    <AchievementPopup
      v-if="latestAchievement"
      :achievement="latestAchievement"
      @close="latestAchievement = null"
    />

    <!-- Purchase Effect -->
    <PurchaseEffect ref="purchaseEffectRef" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, provide, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGamificationStore } from '@/stores/gamification'
import http from '@/services/http'
import AchievementPopup from '@/components/game/AchievementPopup.vue'
import PurchaseEffect from '@/components/game/PurchaseEffect.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const gamificationStore = useGamificationStore()

const currentTheme = ref('default')
const checkedInToday = computed(() => gamificationStore.checkedInToday)
const latestAchievement = ref<any>(null)
const purchaseEffectRef = ref()
const cartCount = ref(0)

// Provide purchase effect trigger globally
provide('triggerPurchaseEffect', (product: any, multiplier: number, goldEarned: number) => {
  purchaseEffectRef.value?.play(product, multiplier, goldEarned)
})
provide('showAchievement', (achievement: any) => {
  latestAchievement.value = achievement
  setTimeout(() => { latestAchievement.value = null }, 4000)
})
// Provide cart count refresh function for child components
provide('refreshCartCount', fetchCartCount)

async function fetchCartCount() {
  if (!authStore.isAuthenticated) return
  try {
    const items = await http.get('/cart')
    cartCount.value = Array.isArray(items) ? items.length : 0
  } catch { cartCount.value = 0 }
}

function goHome() {
  router.push('/shop')
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
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

// Watch for auth changes and route changes to refresh cart count
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

<style>
/* Global resets */
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f0f2f5; color: #303133; }
#jmall-app { min-height: 100vh; display: flex; flex-direction: column; }
</style>

<style scoped>
.jmall-topbar {
  position: sticky; top: 0; z-index: 1000;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0 32px; height: 60px;
  background: #fff; border-bottom: 1px solid #e4e7ed;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.topbar-left { display: flex; align-items: baseline; gap: 12px; cursor: pointer; }
.app-logo { font-size: 22px; font-weight: 800; margin: 0; user-select: none; }
.app-subtitle { font-size: 12px; color: #999; }
.topbar-right { display: flex; align-items: center; gap: 16px; }

.cart-entry {
  cursor: pointer; padding: 6px; border-radius: 8px; transition: background 0.2s;
  position: relative;
}
.cart-entry:hover { background: #f5f7fa; }
.gold-display {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px; background: #fff7e6; border-radius: 20px;
  font-size: 14px; font-weight: 600; color: #e6a23c;
}
.gold-amount { min-width: 50px; }
.user-info {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  padding: 4px 8px; border-radius: 20px; transition: background 0.2s;
}
.user-info:hover { background: #f5f7fa; }
.username { font-size: 14px; color: #303133; max-width: 100px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dropdown-arrow { font-size: 12px; color: #909399; }

.jmall-main { flex: 1; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
