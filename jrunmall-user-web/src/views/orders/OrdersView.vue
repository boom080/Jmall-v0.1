<template>
  <section class="commerce-panel">
    <header class="section-header">
      <div>
        <p class="eyebrow">订单中心</p>
        <h2>我的订单</h2>
        <p>当前统一展示真实登录用户的普通订单与秒杀订单，适合按“下单 -> 支付 -> 秒杀订单查看”顺序演示。</p>
      </div>
      <span class="data-source">{{ orders.length ? '聚合订单接口' : '空态 / 错误态' }}</span>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>

    <div v-if="orders.length" class="order-list">
      <article v-for="order in orders" :key="order.orderRef || order.orderId" class="commerce-card">
        <div class="order-header">
          <div>
            <p class="eyebrow">订单号 {{ order.orderSn }}</p>
            <h3>{{ order.status === 'PAID' ? '已支付订单' : '待支付订单' }}</h3>
            <p class="eyebrow">{{ order.orderSource === 'seckill' ? '秒杀订单' : '普通订单' }}</p>
          </div>
          <strong :class="['status-pill', order.status === 'PAID' ? 'status-pill--success' : 'status-pill--warning']">
            {{ order.status }}
          </strong>
        </div>
        <div class="order-items-preview">
          <div v-for="item in order.items" :key="`${order.orderRef || order.orderId}-${item.skuId}`" class="order-preview-row">
            <img :src="item.coverUrl" :alt="item.title" class="order-preview-row__image" />
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.category }} × {{ item.quantity }}</p>
            </div>
          </div>
        </div>
        <div class="order-footer">
          <span>总金额 ￥{{ order.totalAmount }}</span>
          <RouterLink :to="`/orders/${order.orderRef || order.orderId}`" class="primary-link">查看详情</RouterLink>
        </div>
      </article>
    </div>

    <section v-else class="empty-block">
      <h2>还没有订单</h2>
      <p>先去购物车创建一笔模拟订单，或从秒杀页提交一笔秒杀请求，再回来查看完整订单链路。</p>
      <div class="hero__actions">
        <RouterLink to="/cart" class="primary-link">去购物车</RouterLink>
        <RouterLink to="/seckill" class="secondary-link">去秒杀页</RouterLink>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchOrders } from '@/services/commerce'
import type { OrderSummary } from '@/types/commerce'

const orders = ref<OrderSummary[]>([])
const errorMessage = ref('')

onMounted(async () => {
  try {
    orders.value = await fetchOrders()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '订单列表加载失败'
  }
})
</script>


