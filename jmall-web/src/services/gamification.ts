import http from './http'
import type { CheckinResult, Achievement, LeaderboardEntry, LeaderboardProduct } from '@/types'

export const gamificationApi = {
  checkin(): Promise<CheckinResult> {
    return http.post('/checkin')
  },
  getTodayStatus(): Promise<{ checkedIn: boolean }> {
    return http.get('/checkin/today')
  },
  getAchievements(): Promise<Achievement[]> {
    return http.get('/achievements')
  },
  getTopSpenders(period: 'week' | 'month' | 'all' = 'week'): Promise<LeaderboardEntry[]> {
    return http.get('/leaderboard/spenders', { params: { period } })
  },
  getTopSellers(period: 'week' | 'month' | 'all' = 'week'): Promise<LeaderboardEntry[]> {
    return http.get('/leaderboard/sellers', { params: { period } })
  },
  getTopProducts(period: 'week' | 'month' | 'all' = 'all'): Promise<LeaderboardProduct[]> {
    return http.get('/leaderboard/products', { params: { period } })
  },
}
