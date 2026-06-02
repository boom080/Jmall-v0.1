<template>
  <div class="user-shell">
    <header class="user-shell__header">
      <RouterLink to="/" class="brand">Jrunmall</RouterLink>
      <nav class="user-shell__nav">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/products">商品</RouterLink>
        <RouterLink to="/cart">{{ uiStore.cartLabel }}</RouterLink>
        <RouterLink to="/orders">订单</RouterLink>
        <RouterLink to="/seckill">秒杀</RouterLink>
        <RouterLink to="/account">{{ authStore.isAuthenticated ? '我的' : '登录' }}</RouterLink>
      </nav>
      <div class="user-shell__auth">
        <template v-if="authStore.isAuthenticated">
          <span class="user-shell__user">{{ authStore.displayName }}</span>
          <button type="button" class="secondary-link button-reset" @click="handleLogout">退出</button>
        </template>
        <template v-else>
          <RouterLink to="/login" class="secondary-link">登录</RouterLink>
          <RouterLink to="/register" class="primary-link">注册</RouterLink>
        </template>
      </div>
    </header>

    <main class="user-shell__main">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/store/auth'
import { useUserUiStore } from '@/store/ui'

const router = useRouter()
const uiStore = useUserUiStore()
const authStore = useAuthStore()

async function handleLogout() {
  await authStore.logout()
  uiStore.setCartCount(0)
  await router.push('/login')
}
</script>


