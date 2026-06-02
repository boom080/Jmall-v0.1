<template>
  <section class="seckill-page">
    <header class="seckill-header">
      <div>
        <p class="eyebrow">Jrunmall 秒杀</p>
        <h1>限时抢购</h1>
      </div>
      <div class="seckill-header__status">
        <span>本场进行中</span>
        <strong>抢到后确认地址</strong>
      </div>
    </header>

    <p v-if="errorMessage" class="inline-error">{{ errorMessage }}</p>
    <p v-if="feedbackMessage" class="inline-success">{{ feedbackMessage }}</p>

    <section v-if="deal" class="seckill-offer">
      <div class="seckill-offer__media">
        <img :src="coverUrl" :alt="deal.title" />
      </div>

      <article class="seckill-offer__main">
        <div class="seckill-offer__title">
          <span>{{ deal.category }}</span>
          <h2>{{ deal.title }}</h2>
          <p>{{ deal.summary }}</p>
        </div>

        <div class="seckill-price">
          <span>秒杀价</span>
          <strong>￥{{ deal.price }}</strong>
          <em>限购 {{ deal.limitPerOrder || 1 }} 件</em>
        </div>

        <div class="seckill-service">
          <span>极速锁单</span>
          <span>地址确认</span>
          <span>模拟支付</span>
        </div>

        <div class="seckill-buy-box">
          <div class="quantity-stepper" aria-label="购买数量">
            <button type="button" class="button-reset" :disabled="quantity <= 1" @click="quantity -= 1">-</button>
            <input v-model.number="quantity" type="number" min="1" :max="deal.limitPerOrder || 1" />
            <button type="button" class="button-reset" :disabled="quantity >= maxQuantity" @click="quantity += 1">+</button>
          </div>
          <button type="button" class="seckill-submit button-reset" :disabled="loading" @click="handleSubmit">
            {{ loading ? '提交中...' : '立即抢购' }}
          </button>
        </div>
      </article>
    </section>

    <section v-else-if="!errorMessage" class="empty-block">
      <h2>秒杀商品加载中</h2>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { fetchCurrentSeckillDeal, submitSeckill } from '@/services/seckill'
import type { SeckillDeal } from '@/types/commerce'

const router = useRouter()
const deal = ref<SeckillDeal | null>(null)
const quantity = ref(1)
const loading = ref(false)
const errorMessage = ref('')
const feedbackMessage = ref('')

const coverUrl = computed(() => deal.value?.coverUrl || '/placeholders/products/default-product.svg')
const maxQuantity = computed(() => deal.value?.limitPerOrder || 1)

onMounted(loadDeal)

async function loadDeal() {
  errorMessage.value = ''
  try {
    deal.value = await fetchCurrentSeckillDeal()
    quantity.value = 1
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '秒杀商品加载失败'
  }
}

async function handleSubmit() {
  if (!deal.value) {
    return
  }
  errorMessage.value = ''
  feedbackMessage.value = ''
  const maxQuantity = deal.value.limitPerOrder || 1
  if (!quantity.value || quantity.value < 1 || quantity.value > maxQuantity) {
    errorMessage.value = `购买数量必须在 1 到 ${maxQuantity} 之间`
    return
  }

  loading.value = true
  try {
    const result = await submitSeckill({ quantity: quantity.value })
    if (result.accepted && result.orderId) {
      feedbackMessage.value = '抢购成功，正在进入订单确认。'
      await router.push({ name: 'checkout', query: { seckillOrderId: String(result.orderId) } })
      return
    }
    errorMessage.value = result.message || statusLabel(result.code)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '秒杀请求提交失败'
  } finally {
    loading.value = false
  }
}

function statusLabel(code: string) {
  const labels: Record<string, string> = {
    SOLD_OUT: '本场秒杀商品已售罄',
    DUPLICATE_REQUEST: '你已经提交过本场秒杀',
    NOT_STARTED: '本场秒杀尚未开始',
    ENDED: '本场秒杀已结束',
    ACTIVITY_NOT_FOUND: '秒杀活动尚未就绪',
  }
  return labels[code] || '秒杀请求未受理'
}
</script>
