<template>
  <section class="commerce-panel">
    <header class="section-header">
      <div>
        <p class="eyebrow">订单确认</p>
        <h2>{{ isSeckillCheckout ? '确认秒杀订单' : '提交订单' }}</h2>
        <p>当前下单会绑定真实登录用户与收货地址，并在订单详情中保留地址快照。</p>
      </div>
      <span class="data-source">{{ isSeckillCheckout ? '秒杀订单' : cart.source === 'api' ? '真实购物车' : '本地空态' }}</span>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <p v-if="successMessage" class="inline-success">{{ successMessage }}</p>

    <section v-if="displayItems.length" class="commerce-grid">
      <article class="commerce-card">
        <section>
          <h3>选择收货地址</h3>
          <div v-if="addresses.length" class="stack-form">
            <label v-for="address in addresses" :key="address.id" class="address-choice">
              <input v-model.number="selectedAddressId" type="radio" name="addressId" :value="address.id" />
              <div>
                <strong>{{ address.name }} {{ address.defaultStatus === 1 ? '（默认）' : '' }}</strong>
                <p>{{ address.phone }}</p>
                <p>{{ joinAddress(address) }}</p>
              </div>
            </label>
          </div>
          <div v-else class="empty-block">
            <p>当前还没有收货地址，请先新增地址。</p>
            <RouterLink to="/account/addresses" class="primary-link">去新增地址</RouterLink>
          </div>
        </section>

        <div v-for="item in displayItems" :key="item.skuId" class="cart-item">
          <img :src="item.coverUrl" :alt="item.title" class="cart-item__image" />
          <div class="cart-item__body">
            <h3>{{ item.title }}</h3>
            <p>{{ item.category }}</p>
            <p>{{ item.summary }}</p>
            <strong>￥{{ item.price }} × {{ item.quantity }}</strong>
          </div>
          <strong>￥{{ item.totalAmount }}</strong>
        </div>
      </article>

      <aside class="commerce-card commerce-card--summary">
        <label class="form-field">
          <span>订单备注</span>
          <textarea v-model="note" rows="4" maxlength="120" placeholder="可选：给商家或自己备注本次演示订单" />
        </label>
        <dl class="summary-list">
          <div>
            <dt>当前用户</dt>
            <dd>{{ displayName }}</dd>
          </div>
          <div>
            <dt>商品件数</dt>
            <dd>{{ totalCount }}</dd>
          </div>
          <div>
            <dt>应付金额</dt>
            <dd>￥{{ totalAmount }}</dd>
          </div>
        </dl>
        <button type="button" class="primary-link button-reset" :disabled="submitting || !selectedAddressId" @click="submitOrder">
          {{ submitting ? '提交中...' : isSeckillCheckout ? '确认地址' : '提交订单' }}
        </button>
      </aside>
    </section>

    <section v-else class="empty-block">
      <h2>购物车为空</h2>
      <p>请先添加商品，再进入下单确认页。</p>
      <RouterLink to="/products" class="primary-link">去逛商品</RouterLink>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { fetchAddresses } from '@/services/addresses'
import { confirmOrderAddress, createOrder, fetchCartItems, fetchOrderById } from '@/services/commerce'
import { useAuthStore } from '@/store/auth'
import { useUserUiStore } from '@/store/ui'
import type { UserAddress } from '@/types/auth'
import type { CartItem, CartSnapshot, OrderSummary } from '@/types/commerce'

const router = useRouter()
const route = useRoute()
const uiStore = useUserUiStore()
const authStore = useAuthStore()
const addresses = ref<UserAddress[]>([])
const selectedAddressId = ref<number | null>(null)
const seckillOrder = ref<OrderSummary | null>(null)
const cart = reactive<CartSnapshot>({
  source: 'fallback',
  userId: 0,
  displayName: '',
  totalCount: 0,
  totalAmount: 0,
  items: [],
})
const note = ref('')
const submitting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

onMounted(async () => {
  await Promise.all([isSeckillCheckout.value ? loadSeckillOrder() : loadCart(), loadAddresses()])
})

const isSeckillCheckout = computed(() => Boolean(route.query.seckillOrderId))
const displayItems = computed<CartItem[]>(() => {
  if (!isSeckillCheckout.value || !seckillOrder.value) {
    return cart.items
  }
  return seckillOrder.value.items.map((item) => ({
    skuId: item.skuId,
    title: item.title,
    category: item.category,
    price: item.price,
    quantity: item.quantity,
    coverUrl: item.coverUrl || '/placeholders/products/default-product.svg',
    summary: item.summary,
    totalAmount: item.lineAmount,
  }))
})
const totalCount = computed(() => (isSeckillCheckout.value ? seckillOrder.value?.totalQuantity || 0 : cart.totalCount))
const totalAmount = computed(() => (isSeckillCheckout.value ? seckillOrder.value?.totalAmount || 0 : cart.totalAmount))
const displayName = computed(() => (isSeckillCheckout.value ? seckillOrder.value?.username || authStore.displayName : cart.displayName || authStore.displayName))

async function loadSeckillOrder() {
  const orderId = String(route.query.seckillOrderId || '')
  if (!orderId) {
    errorMessage.value = '秒杀订单不存在'
    return
  }
  try {
    seckillOrder.value = await fetchOrderById(orderId)
    if (seckillOrder.value.orderSource !== 'seckill') {
      errorMessage.value = '该订单不是秒杀订单'
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '秒杀订单加载失败'
  }
}

async function loadCart() {
  const result = await fetchCartItems()
  cart.source = result.source
  cart.userId = result.userId
  cart.displayName = result.displayName
  cart.totalCount = result.totalCount
  cart.totalAmount = result.totalAmount
  cart.items = result.items
  cart.errorMessage = result.errorMessage
  errorMessage.value = result.errorMessage || ''
  uiStore.setCartCount(result.totalCount)
}

async function loadAddresses() {
  addresses.value = await fetchAddresses()
  const defaultAddress = addresses.value.find((item) => item.defaultStatus === 1)
  selectedAddressId.value = Number(defaultAddress?.id || addresses.value[0]?.id || 0) || null
}

async function submitOrder() {
  if (!selectedAddressId.value) {
    errorMessage.value = '请先选择收货地址'
    return
  }
  submitting.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const order = isSeckillCheckout.value && seckillOrder.value
      ? await confirmOrderAddress(seckillOrder.value.orderId, selectedAddressId.value, note.value)
      : await createOrder(selectedAddressId.value, note.value)
    if (!isSeckillCheckout.value) {
      uiStore.setCartCount(0)
    }
    successMessage.value = '订单已确认，正在跳转到支付页面'
    await router.push(`/orders/${order.orderId}`)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '创建订单失败'
  } finally {
    submitting.value = false
  }
}

function joinAddress(address: UserAddress) {
  return [address.province, address.city, address.region, address.detailAddress].filter(Boolean).join('')
}
</script>


