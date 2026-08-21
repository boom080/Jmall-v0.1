<template>
  <div class="dashboard">
    <h2>📊 工作台</h2>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="8"><el-skeleton><template #template><el-skeleton-item variant="rect" style="height:160px;border-radius:16px" /></template></el-skeleton></el-col>
        <el-col :span="8"><el-skeleton><template #template><el-skeleton-item variant="rect" style="height:160px;border-radius:16px" /></template></el-skeleton></el-col>
        <el-col :span="8"><el-skeleton><template #template><el-skeleton-item variant="rect" style="height:160px;border-radius:16px" /></template></el-skeleton></el-col>
      </el-row>
    </div>

    <!-- Error State -->
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadDashboard">🔄 重新加载</el-button>
      </template>
    </el-result>

    <template v-else>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="8">
        <el-card
          shadow="hover"
          class="stat-card stat-card-link"
          role="button"
          tabindex="0"
          aria-label="进入我的店铺查看已上架商品"
          @click="openMyStore"
          @keyup.enter="openMyStore"
        >
          <div class="stat-icon">🛍️</div>
          <div class="stat-value">{{ stats.productCount }}</div>
          <div class="stat-label">已上架商品</div>
          <div class="stat-hint">点击进入我的店铺 →</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">💰</div>
          <div class="stat-value">{{ formatViews(stats.totalSales) }}</div>
          <div class="stat-label">累计售出</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-icon">🧾</div>
          <div class="stat-value">{{ formatViews(stats.totalOrders) }}</div>
          <div class="stat-label">累计订单</div>
        </el-card>
      </el-col>
    </el-row>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><h3>🤖 AI 功能概览</h3></template>
          <el-steps direction="vertical">
            <el-step title="📝 文案生成" description="支持5大平台风格文案生成" />
            <el-step title="📈 市场调研" description="实时搜索行业趋势和热搜词" />
            <el-step title="⚖️ 合规审查" description="自动检测价格异常和违规内容" />
            <el-step title="🎨 风格预览" description="一键预览不同平台商品页效果" />
          </el-steps>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="never">
          <template #header><h3>📖 快速入门</h3></template>
          <el-steps direction="vertical">
            <el-step title="1. 创建店铺" description="在「店铺装修」设置你的店铺信息" />
            <el-step title="2. 上架商品" description="去「商品管理」用 AI Agent 辅助上架" />
            <el-step title="3. 上传知识库" description="在「知识库」上传行业资料，提升 AI 文案质量" />
            <el-step title="4. 查看效果" description="切换到买家模式查看商品页效果" />
          </el-steps>
        </el-card>
      </el-col>
    </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { storeApi } from '@/services/stores'

const router = useRouter()
const loading = ref(true)
const error = ref<string | null>(null)

const stats = ref({
  storeId: 0,
  productCount: 0,
  totalSales: 0,
  totalOrders: 0,
})

function formatViews(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

function openMyStore() {
  if (!stats.value.storeId) {
    ElMessage.warning('请先在“店铺装修”中创建店铺')
    return
  }
  router.push(`/store/${stats.value.storeId}`)
}

onMounted(() => { loadDashboard() })

async function loadDashboard() {
  loading.value = true
  error.value = null
  try {
    const result = await storeApi.getMyStats()
    stats.value.storeId = Number(result.storeId || 0)
    stats.value.productCount = result.productCount || 0
    stats.value.totalSales = result.totalSales || 0
    stats.value.totalOrders = result.totalOrders || 0
  } catch (e: any) {
    error.value = e.message || '工作台数据加载失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.dashboard { padding: 24px; }
.stat-card { text-align: center; border-radius: 16px; cursor: pointer; transition: transform 0.2s; }
.stat-card:hover { transform: translateY(-4px); }
.stat-card-link:focus-visible { outline: 3px solid rgba(64, 158, 255, 0.35); outline-offset: 3px; }
.stat-icon { font-size: 40px; margin-bottom: 8px; }
.stat-value { font-size: 28px; font-weight: bold; color: var(--primary); }
.stat-label { font-size: 14px; color: #999; margin-top: 4px; }
.stat-hint { margin-top: 8px; font-size: 12px; color: #409eff; }
.loading-state { padding: 24px 0; }
</style>
