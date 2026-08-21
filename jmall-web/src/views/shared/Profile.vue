<template>
  <div class="profile-page">
    <h2>👤 个人中心</h2>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- Error State -->
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadProfile">🔄 重新加载</el-button>
      </template>
    </el-result>

    <template v-else>
      <!-- User Info Card -->
      <el-card shadow="never" class="profile-card">
        <div class="profile-header">
          <el-avatar :size="64" icon="UserFilled" />
          <div class="profile-info">
            <h3>{{ profile.nickname || profile.username }}</h3>
            <p class="username">@{{ profile.username }}</p>
            <el-tag :type="profile.role === 'admin' ? 'danger' : ''" size="small">
              {{ profile.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </div>
          <div class="profile-stats">
            <div class="stat-item">
              <span class="stat-num">🪙 {{ formatNumber(profile.goldBalance) }}</span>
              <span class="stat-text">金币余额</span>
            </div>
            <div class="stat-item">
              <span class="stat-num">🔥 {{ profile.checkinStreak || 0 }} 天</span>
              <span class="stat-text">连续签到</span>
            </div>
            <div class="stat-item">
              <el-button type="warning" @click="doCheckin" :disabled="checkedInToday" :loading="checkinLoading">
                {{ checkedInToday ? '✅ 已签到' : '📅 每日签到' }}
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Quick Actions -->
      <el-row :gutter="16" style="margin-top: 24px">
        <el-col :span="8">
          <el-card shadow="hover" class="action-card" @click="$router.push('/achievements')">
            <div class="action-icon">🏆</div>
            <div class="action-label">成就墙</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="action-card" @click="$router.push('/collections')">
            <div class="action-icon">❤️</div>
            <div class="action-label">我的拥有</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="action-card" @click="$router.push('/leaderboard')">
            <div class="action-icon">📊</div>
            <div class="action-label">排行榜</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- Gold Transaction History -->
      <el-card shadow="never" style="margin-top: 24px">
        <template #header>
          <h3 style="margin: 0">💰 金币流水</h3>
        </template>

        <div v-if="ledgerLoading" class="loading-state">
          <el-skeleton :rows="3" animated />
        </div>
        <el-empty v-else-if="ledger.length === 0" description="暂无收支记录" />

        <el-timeline v-else>
          <el-timeline-item
            v-for="item in ledger"
            :key="item.id"
            :timestamp="formatDateTime(item.createdAt)"
            :type="item.amount > 0 ? 'success' : 'danger'"
            :icon="item.amount > 0 ? 'Plus' : 'Minus'"
          >
            <div class="ledger-item">
              <span :class="item.amount > 0 ? 'amount-positive' : 'amount-negative'">
                {{ item.amount > 0 ? '+' : '' }}{{ formatNumber(item.amount) }} 🪙
              </span>
              <span class="ledger-desc">{{ item.description }}</span>
              <el-tag size="small" type="info">{{ labelForType(item.type) }}</el-tag>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGamificationStore } from '@/stores/gamification'
import http from '@/services/http'
import { ElMessage } from 'element-plus'

const router = useRouter()
const authStore = useAuthStore()
const gamificationStore = useGamificationStore()

const loading = ref(true)
const error = ref<string | null>(null)
const ledgerLoading = ref(false)
const checkinLoading = ref(false)
const checkedInToday = ref(false)

const profile = ref({
  id: 0,
  username: '',
  nickname: '',
  role: '',
  goldBalance: 0,
  pointsBalance: 0,
  checkinStreak: 0,
})

const ledger = ref<any[]>([])

function formatNumber(n: number): string {
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return n.toLocaleString()
}

function formatDateTime(d: string): string {
  if (!d) return '-'
  return new Date(d).toLocaleString('zh-CN')
}

function labelForType(type: string): string {
  const labels: Record<string, string> = {
    purchase: '购买支出',
    sale: '销售收入',
    checkin: '签到奖励',
    bonus: '成就奖励',
    ai_cost: 'AI 服务',
    refund: '退款',
  }
  return labels[type] || type
}

async function loadProfile() {
  loading.value = true
  error.value = null
  try {
    const user: any = await http.get('/user/profile')
    profile.value = user
    authStore.currentUser = user
  } catch (e: any) {
    error.value = e.message || '加载用户信息失败'
  } finally {
    loading.value = false
  }
}

async function loadLedger() {
  ledgerLoading.value = true
  try {
    ledger.value = await http.get('/user/gold-ledger') as any
  } catch {
    ledger.value = []
  } finally {
    ledgerLoading.value = false
  }
}

async function checkTodayStatus() {
  try {
    const status: any = await http.get('/checkin/today')
    checkedInToday.value = status.checkedIn || false
  } catch { /* ignore */ }
}

async function doCheckin() {
  checkinLoading.value = true
  try {
    const result = await gamificationStore.checkin()
    checkedInToday.value = true
    profile.value.goldBalance = authStore.goldBalance
    ElMessage.success(`🎉 签到成功! +${result.goldReward} 金币，连续 ${result.streakDay} 天`)
    await loadLedger()
  } catch (e: any) {
    ElMessage.error(e.message || '签到失败')
  } finally {
    checkinLoading.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadProfile(), checkTodayStatus(), loadLedger()])
})
</script>

<style scoped>
.profile-page { padding: 40px; max-width: 900px; margin: 0 auto; }
.profile-card { border-radius: 16px; }
.profile-header { display: flex; align-items: center; gap: 20px; }
.profile-info h3 { margin: 0; font-size: 22px; }
.profile-info .username { color: #999; margin: 4px 0 8px; }
.profile-stats { margin-left: auto; display: flex; gap: 32px; align-items: center; }
.stat-item { text-align: center; }
.stat-num { display: block; font-size: 18px; font-weight: bold; }
.stat-text { display: block; font-size: 12px; color: #999; margin-top: 4px; }

.action-card {
  text-align: center; border-radius: 16px; cursor: pointer;
  transition: transform 0.2s;
}
.action-card:hover { transform: translateY(-4px); }
.action-icon { font-size: 36px; margin-bottom: 8px; }
.action-label { font-size: 14px; color: #666; }

.ledger-item { display: flex; align-items: center; gap: 12px; }
.amount-positive { color: #67c23a; font-weight: bold; }
.amount-negative { color: #f56c6c; font-weight: bold; }
.ledger-desc { color: #666; font-size: 14px; flex: 1; }

.loading-state { padding: 24px; }
</style>
