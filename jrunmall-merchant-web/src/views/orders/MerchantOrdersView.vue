<template>
  <section class="merchant-page-grid merchant-page-grid--single">
    <el-card shadow="never">
      <template #header>
        <div class="table-header">
          <div>
            <p class="table-eyebrow">Orders</p>
            <h2>用户端订单列表</h2>
          </div>
          <el-tag>只读最小版</el-tag>
        </div>
      </template>

      <el-alert v-if="errorMessage" type="error" :closable="false" class="merchant-alert" :title="errorMessage" />

      <el-table v-if="orders.length" :data="orders" style="width: 100%">
        <el-table-column prop="orderSn" label="订单号" min-width="220" />
        <el-table-column prop="username" label="用户" width="160" />
        <el-table-column prop="status" label="订单状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'PAID' ? 'success' : 'warning'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="totalAmount" label="总金额" width="140">
          <template #default="{ row }">¥{{ row.totalAmount }}</template>
        </el-table-column>
        <el-table-column prop="paymentTime" label="支付时间" min-width="180">
          <template #default="{ row }">{{ row.paymentTime || '未支付' }}</template>
        </el-table-column>
      </el-table>

      <el-empty v-else description="当前还没有可展示的订单" />
    </el-card>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { fetchMerchantOrders } from '@/services/merchantOrders'
import type { MerchantOrderSummary } from '@/types/merchant'

const orders = ref<MerchantOrderSummary[]>([])
const errorMessage = ref('')

onMounted(async () => {
  try {
    orders.value = await fetchMerchantOrders()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '订单列表加载失败'
  }
})
</script>


