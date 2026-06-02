<template>
  <section v-if="order" class="commerce-panel">
    <header class="section-header">
      <div>
        <p class="eyebrow">订单详情</p>
        <h2>订单 {{ order.orderSn }}</h2>
        <p>普通订单与秒杀订单都使用同一套地址确认和模拟支付流程。</p>
      </div>
      <strong :class="['status-pill', order.status === 'PAID' ? 'status-pill--success' : 'status-pill--warning']">
        {{ order.status }}
      </strong>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="inline-success">{{ successMessage }}</p>

    <section class="commerce-grid">
      <article class="commerce-card">
        <div v-for="item in order.items" :key="`${order.orderRef || order.orderId}-${item.skuId}`" class="cart-item">
          <img :src="item.coverUrl" :alt="item.title" class="cart-item__image" />
          <div class="cart-item__body">
            <h3>{{ item.title }}</h3>
            <p>{{ item.category }}</p>
            <p>{{ item.summary }}</p>
            <strong>￥{{ item.price }} × {{ item.quantity }}</strong>
          </div>
          <strong>￥{{ item.lineAmount }}</strong>
        </div>
      </article>

      <aside class="commerce-card commerce-card--summary">
        <dl class="summary-list">
          <div>
            <dt>订单来源</dt>
            <dd>{{ order.orderSource === 'seckill' ? '秒杀订单' : '普通订单' }}</dd>
          </div>
          <div>
            <dt>订单状态</dt>
            <dd>{{ order.status }}</dd>
          </div>
          <div>
            <dt>商品件数</dt>
            <dd>{{ order.totalQuantity }}</dd>
          </div>
          <div>
            <dt>应付金额</dt>
            <dd>￥{{ order.totalAmount }}</dd>
          </div>
          <div v-if="order.receiverName || order.receiverAddress">
            <dt>收货信息</dt>
            <dd>{{ order.receiverName }} {{ order.receiverPhone }} {{ order.receiverAddress }}</dd>
          </div>
          <div>
            <dt>创建时间</dt>
            <dd>{{ order.createdTime }}</dd>
          </div>
          <div>
            <dt>支付时间</dt>
            <dd>{{ order.paymentTime || '未支付' }}</dd>
          </div>
        </dl>
        <button
          v-if="needsAddress"
          type="button"
          class="primary-link button-reset"
          @click="goConfirmAddress"
        >
          填写收货地址
        </button>
        <button
          v-else-if="order.status === 'CREATED'"
          type="button"
          class="primary-link button-reset"
          :disabled="paying"
          @click="handlePay"
        >
          {{ paying ? '支付中...' : '立即模拟支付' }}
        </button>
        <RouterLink v-else to="/orders" class="primary-link">返回订单列表</RouterLink>
      </aside>
    </section>
  </section>
  <section v-else class="empty-block">
    <h2>订单不存在</h2>
    <p v-if="errorMessage">{{ errorMessage }}</p>
    <RouterLink to="/orders" class="primary-link">返回订单列表</RouterLink>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchOrderById, payOrder } from '@/services/commerce'
import type { OrderSummary } from '@/types/commerce'

const route = useRoute()
const router = useRouter()
const order = ref<OrderSummary | null>(null)
const errorMessage = ref('')
const successMessage = ref('')
const paying = ref(false)
const needsAddress = computed(() => Boolean(order.value && order.value.status === 'CREATED' && !order.value.receiverAddress))

onMounted(loadOrder)

async function loadOrder() {
  try {
    order.value = await fetchOrderById(String(route.params.orderRef ?? route.params.orderId))
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '订单详情加载失败'
  }
}

async function handlePay() {
  if (!order.value) {
    return
  }
  paying.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    order.value = await payOrder(order.value.orderId)
    successMessage.value = '模拟支付成功，订单已更新为已支付。'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '模拟支付失败'
  } finally {
    paying.value = false
  }
}

async function goConfirmAddress() {
  if (!order.value) {
    return
  }
  await router.push({ name: 'checkout', query: { seckillOrderId: String(order.value.orderId) } })
}
</script>


