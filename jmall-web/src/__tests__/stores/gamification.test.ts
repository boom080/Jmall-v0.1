/** Tests for the gamification Pinia store.
 *
 * Covers: checkin flow, achievement loading, today status check,
 * store state transitions.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useGamificationStore } from '@/stores/gamification'

// Mock the gamification API module
vi.mock('@/services/gamification', () => ({
  gamificationApi: {
    checkin: vi.fn(),
    getTodayStatus: vi.fn(),
    getAchievements: vi.fn(),
  },
}))

import { gamificationApi } from '@/services/gamification'

function mockCheckinResponse(overrides: Record<string, unknown> = {}) {
  return {
    goldReward: 700,
    streakDay: 3,
    totalGold: 10700,
    newAchievements: [],
    ...overrides,
  }
}

function mockAchievements() {
  return [
    { key: 'FIRST_PURCHASE', name: '初次购买', description: '完成第一次购买', unlocked: true, icon: '💰' },
    { key: 'COLLECTOR_10', name: '收藏家', description: '收藏10件商品', unlocked: false, icon: '⭐' },
    { key: 'STREAK_7', name: '连续签到', description: '连续签到7天', unlocked: false, icon: '🔥' },
  ]
}

describe('useGamificationStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('starts with empty achievements', () => {
      const store = useGamificationStore()
      expect(store.achievements).toEqual([])
    })

    it('starts with checkedInToday = false', () => {
      const store = useGamificationStore()
      expect(store.checkedInToday).toBe(false)
    })
  })

  describe('checkin', () => {
    it('marks checkedInToday as true after successful checkin', async () => {
      vi.mocked(gamificationApi.checkin).mockResolvedValue(mockCheckinResponse())

      const store = useGamificationStore()
      await store.checkin()

      expect(store.checkedInToday).toBe(true)
    })

    it('returns checkin result with gold reward', async () => {
      vi.mocked(gamificationApi.checkin).mockResolvedValue(
        mockCheckinResponse({ goldReward: 900, streakDay: 5 })
      )

      const store = useGamificationStore()
      const result = await store.checkin()

      expect(result.goldReward).toBe(900)
      expect(result.streakDay).toBe(5)
      expect(result.totalGold).toBe(10700)
    })

    it('reloads achievements after checkin', async () => {
      vi.mocked(gamificationApi.checkin).mockResolvedValue(mockCheckinResponse())
      const mockAchs = mockAchievements()
      vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchs)

      const store = useGamificationStore()
      await store.checkin()

      expect(gamificationApi.getAchievements).toHaveBeenCalled()
      expect(store.achievements.length).toBe(3)
    })

    it('identifies unlocked achievements', async () => {
      vi.mocked(gamificationApi.checkin).mockResolvedValue(mockCheckinResponse())
      const achs = mockAchievements()
      vi.mocked(gamificationApi.getAchievements).mockResolvedValue(achs)

      const store = useGamificationStore()
      await store.checkin()

      const unlocked = store.achievements.filter(a => a.unlocked)
      expect(unlocked.length).toBe(1)
      expect(unlocked[0].key).toBe('FIRST_PURCHASE')
    })
  })

  describe('checkTodayStatus', () => {
    it('sets checkedInToday from API response', async () => {
      vi.mocked(gamificationApi.getTodayStatus).mockResolvedValue({ checkedIn: true })

      const store = useGamificationStore()
      await store.checkTodayStatus()

      expect(store.checkedInToday).toBe(true)
    })

    it('keeps false when API says not checked in', async () => {
      vi.mocked(gamificationApi.getTodayStatus).mockResolvedValue({ checkedIn: false })

      const store = useGamificationStore()
      await store.checkTodayStatus()

      expect(store.checkedInToday).toBe(false)
    })

    it('handles API error gracefully', async () => {
      vi.mocked(gamificationApi.getTodayStatus).mockRejectedValue(new Error('Network error'))

      const store = useGamificationStore()
      await store.checkTodayStatus()

      // Should not throw, checkedInToday stays false
      expect(store.checkedInToday).toBe(false)
    })
  })

  describe('loadAchievements', () => {
    it('loads achievements from API', async () => {
      vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievements())

      const store = useGamificationStore()
      await store.loadAchievements()

      expect(store.achievements).toHaveLength(3)
      expect(store.achievements[0].key).toBe('FIRST_PURCHASE')
    })

    it('handles API error by setting empty array', async () => {
      vi.mocked(gamificationApi.getAchievements).mockRejectedValue(new Error('Network error'))

      const store = useGamificationStore()
      await store.loadAchievements()

      expect(store.achievements).toEqual([])
    })

    it('loads achievement details correctly', async () => {
      vi.mocked(gamificationApi.getAchievements).mockResolvedValue(mockAchievements())

      const store = useGamificationStore()
      await store.loadAchievements()

      const first = store.achievements[0]
      expect(first.name).toBe('初次购买')
      expect(first.description).toBeTruthy()
      expect(typeof first.unlocked).toBe('boolean')
    })
  })
})
