<template>
  <div class="merchant-shell">
    <aside class="merchant-shell__sidebar">
      <div class="merchant-shell__brand">Jrunmall Merchant</div>
      <RouterLink to="/products">商品管理</RouterLink>
      <RouterLink to="/knowledge-bases">知识库管理</RouterLink>
      <RouterLink to="/orders">普通订单</RouterLink>
      <RouterLink to="/seckill-orders">秒杀订单</RouterLink>
    </aside>

    <div class="merchant-shell__content">
      <header class="merchant-shell__header">
        <h1>{{ route.meta.title || uiStore.appTitle }}</h1>
      </header>
      <main class="merchant-shell__main">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

import { useMerchantUiStore } from '@/store/ui'

const route = useRoute()
const uiStore = useMerchantUiStore()
</script>
