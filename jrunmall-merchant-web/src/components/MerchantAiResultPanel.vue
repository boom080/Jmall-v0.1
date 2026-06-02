<template>
  <section class="result-panel">
    <div class="result-panel__header">
      <div>
        <p class="result-panel__label">生成结果</p>
        <h3>{{ result.generatedTitle }}</h3>
      </div>
      <div class="result-panel__tags">
        <el-tag :type="result.success ? 'success' : 'warning'">
          {{ result.success ? '成功结果' : '降级结果' }}
        </el-tag>
        <el-tag type="info">{{ result.provider }}</el-tag>
        <el-tag :type="result.response_source === 'rag' ? 'success' : 'warning'">{{ result.response_source }}</el-tag>
        <el-tag v-if="result.mock" type="info">Mock</el-tag>
      </div>
    </div>

    <el-alert
      v-if="!result.success"
      type="warning"
      :closable="false"
      show-icon
      title="当前结果来自后端降级返回"
      :description="result.message"
    />

    <div class="result-panel__cards">
      <el-card shadow="never">
        <template #header>摘要</template>
        <p>{{ result.summary }}</p>
      </el-card>
      <el-card shadow="never">
        <template #header>卖点</template>
        <ul class="result-panel__highlights">
          <li v-for="item in result.highlights" :key="item">{{ item }}</li>
        </ul>
      </el-card>
    </div>

    <el-card
      v-if="result.pendingMerchantConfirmations?.length"
      shadow="never"
      class="result-panel__confirmations"
    >
      <template #header>待商家确认信息</template>
      <ul class="result-panel__confirm-list">
        <li v-for="item in result.pendingMerchantConfirmations" :key="item">{{ item }}</li>
      </ul>
    </el-card>

    <el-alert
      v-if="result.embeddingProvider === 'mock-embedding'"
      type="warning"
      :closable="false"
      show-icon
      class="result-panel__alert"
      title="当前为开发测试向量，非真实语义检索效果。"
    />

    <el-alert
      v-else-if="result.embeddingProvider === 'openai-compatible' || result.embeddingProvider === 'openai-compatible-embedding'"
      type="success"
      :closable="false"
      show-icon
      class="result-panel__alert"
      title="当前使用真实 embedding provider。"
    />

    <el-card v-if="result.usedChunks?.length" shadow="never" class="result-panel__sources">
      <template #header>引用来源</template>
      <ul class="result-panel__chunks">
        <li v-for="chunk in result.usedChunks" :key="chunk.chunkId">
          <strong>{{ chunk.sourceFilename || chunk.documentId }}</strong>
          <span>Chunk {{ chunk.chunkIndex }} / {{ Number(chunk.score || 0).toFixed(4) }}</span>
          <p>{{ chunk.content }}</p>
        </li>
      </ul>
    </el-card>
  </section>
</template>

<script setup lang="ts">
import type { ProductAiResult } from '@/types/productAi'

defineProps<{
  result: ProductAiResult
}>()
</script>

<style scoped>
.result-panel__alert,
.result-panel__confirmations,
.result-panel__sources {
  margin-top: 12px;
}

.result-panel__confirm-list {
  margin: 0;
  padding-left: 18px;
  color: #92400e;
  line-height: 1.7;
}

.result-panel__chunks {
  margin: 0;
  padding-left: 18px;
}

.result-panel__chunks li {
  margin-bottom: 10px;
}

.result-panel__chunks span {
  color: #64748b;
  margin-left: 8px;
  font-size: 12px;
}

.result-panel__chunks p {
  margin: 4px 0 0;
  color: #334155;
  line-height: 1.6;
}
</style>
