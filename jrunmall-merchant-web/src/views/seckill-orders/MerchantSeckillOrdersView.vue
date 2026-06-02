<template>
  <section class="merchant-page-grid merchant-page-grid--single">
    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <div>
            <p class="table-eyebrow">Seckill Orders</p>
            <h2>秒杀订单只读查看</h2>
          </div>
          <el-tag type="info">只读最小版</el-tag>
        </div>
      </template>

      <el-alert v-if="errorMessage" type="error" :closable="false" class="merchant-alert" :title="errorMessage" />

      <el-table v-if="orders.length" :data="orders" style="width: 100%">
        <el-table-column prop="orderSn" label="订单号" min-width="220" />
        <el-table-column prop="userId" label="用户标识" width="120" />
        <el-table-column prop="title" label="商品标题" min-width="180" />
        <el-table-column prop="quantity" label="数量" width="90" />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'PAID' ? 'success' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="110">
          <template #default="{ row }">
            <el-tag type="danger">{{ row.source }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" min-width="180" />
      </el-table>

      <el-empty v-else description="当前没有秒杀订单" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchMerchantSeckillOrders } from '@/services/merchantSeckillOrders'
import type { MerchantSeckillOrderSummary } from '@/types/merchant'

const orders = ref<MerchantSeckillOrderSummary[]>([])
const errorMessage = ref('')

onMounted(async () => {
  try {
    orders.value = await fetchMerchantSeckillOrders()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '秒杀订单加载失败'
  }
})
</script>


