<template>
  <div class="achievements-page">
    <h2>🏆 成就墙</h2>
    <p class="subtitle">已解锁 {{ unlocked.length }} / {{ total }} 项成就</p>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- Error State -->
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="loadAchievements">🔄 重新加载</el-button>
      </template>
    </el-result>

    <div v-else class="achievements-grid">
      <div v-for="ach in achievements" :key="ach.key" class="achievement-card" :class="{ locked: !ach.unlocked }">
        <div class="ach-icon">{{ ach.unlocked ? getIcon(ach.key) : '🔒' }}</div>
        <div class="ach-name">{{ ach.unlocked ? ach.name : '???' }}</div>
        <div class="ach-desc">{{ ach.unlocked ? ach.description : '继续探索解锁此成就' }}</div>
        <div v-if="ach.goldBonus > 0" class="ach-bonus">+{{ ach.goldBonus }} 🪙</div>
        <div v-if="ach.unlockedAt" class="ach-date">{{ formatDate(ach.unlockedAt) }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ACHIEVEMENT_ICONS, type Achievement } from '@/types'
import { useGamificationStore } from '@/stores/gamification'

const achievements = ref<Achievement[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const total = computed(() => achievements.value.length)
const unlocked = computed(() => achievements.value.filter(a => a.unlocked))

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('zh-CN')
}

function getIcon(key: string): string {
  return ACHIEVEMENT_ICONS[key] || '🏆'
}

onMounted(() => { loadAchievements() })

async function loadAchievements() {
  loading.value = true
  error.value = null
  try {
    const store = useGamificationStore()
    await store.loadAchievements()
    achievements.value = store.achievements
  } catch (e: any) {
    error.value = e.message || '加载成就数据失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.achievements-page { padding: 40px; max-width: 1000px; margin: 0 auto; }
.subtitle { color: #999; margin-bottom: 24px; }
.achievements-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.achievement-card {
  background: white; border-radius: 16px; padding: 24px;
  text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: transform 0.2s;
}
.achievement-card.locked { opacity: 0.5; filter: grayscale(100%); }
.achievement-card:not(.locked):hover { transform: translateY(-4px); }
.ach-icon { font-size: 40px; margin-bottom: 8px; }
.ach-name { font-weight: bold; font-size: 15px; margin-bottom: 4px; }
.ach-desc { font-size: 13px; color: #666; }
.ach-bonus { font-size: 13px; color: #f39c12; font-weight: bold; margin-top: 4px; }
.ach-date { font-size: 12px; color: #999; margin-top: 8px; }
.loading-state { padding: 40px 0; }
</style>
