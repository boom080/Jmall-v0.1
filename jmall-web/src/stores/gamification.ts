import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CheckinResult, Achievement } from '@/types'
import { gamificationApi } from '@/services/gamification'
export { gamificationApi }

export const useGamificationStore = defineStore('gamification', () => {
  const achievements = ref<Achievement[]>([])
  const checkedInToday = ref(false)

  async function checkin(): Promise<CheckinResult> {
    const result = await gamificationApi.checkin()
    checkedInToday.value = true
    // Check for new achievements
    await loadAchievements()
    return result
  }

  async function checkTodayStatus() {
    try {
      const status = await gamificationApi.getTodayStatus()
      checkedInToday.value = status.checkedIn
    } catch { /* ignore */ }
  }

  async function loadAchievements() {
    try {
      achievements.value = await gamificationApi.getAchievements()
    } catch { achievements.value = [] }
  }

  return { achievements, checkedInToday, checkin, checkTodayStatus, loadAchievements }
})
