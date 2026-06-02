<template>
  <section class="commerce-panel">
    <header class="section-header">
      <div>
        <p class="eyebrow">我的</p>
        <h2>用户中心</h2>
        <p>当前用户端已经从 Demo 用户过渡到最小真实登录态，地址管理与下单地址绑定同步接入。</p>
      </div>
    </header>

    <section class="commerce-grid">
      <article class="commerce-card commerce-card--summary">
        <h3>{{ authStore.displayName }}</h3>
        <p>用户名：{{ authStore.currentUser?.username }}</p>
        <p>用户 ID：{{ authStore.currentUser?.userId }}</p>
      </article>

      <article class="commerce-card">
        <h3>演示快捷入口</h3>
        <div class="hero__actions">
          <RouterLink to="/cart" class="primary-link">去购物车</RouterLink>
          <RouterLink to="/seckill" class="secondary-link">去秒杀页</RouterLink>
        </div>
        <div class="hero__actions" style="margin-top: 12px">
          <RouterLink to="/orders" class="primary-link">查看订单</RouterLink>
          <RouterLink to="/account/addresses" class="secondary-link">地址管理</RouterLink>
        </div>
      </article>
    </section>
  </section>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/store/auth'

const authStore = useAuthStore()
</script>


