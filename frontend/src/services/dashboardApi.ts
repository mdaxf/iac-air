import api from './api'
import type {
  DashboardStats,
  DashboardData,
  RecentActivity,
  SystemHealth,
  SystemConfiguration
} from '@/types'

export const dashboardApi = {
  // Get dashboard statistics
  getStats: () =>
    api.get<DashboardStats>('/dashboard/stats'),

  // Get complete dashboard data (stats + recent activities)
  getDashboardData: () =>
    api.get<DashboardData>('/dashboard/'),

  // Get recent activities
  getRecentActivities: (limit: number = 20) =>
    api.get<RecentActivity[]>('/dashboard/recent-activities', {
      params: { limit }
    }),

  // Get system health (admin only)
  getSystemHealth: () =>
    api.get<SystemHealth>('/dashboard/system-health'),

  // Get system configuration (admin only)
  getSystemConfiguration: () =>
    api.get<SystemConfiguration>('/dashboard/system-config')
}