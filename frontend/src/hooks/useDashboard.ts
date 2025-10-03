import { useQuery } from 'react-query'
import { dashboardApi } from '@/services/dashboardApi'
import type {
  DashboardStats,
  DashboardData,
  RecentActivity,
  SystemHealth,
  SystemConfiguration
} from '@/types'

// Dashboard Stats Hook
export function useDashboardStats() {
  return useQuery(
    'dashboardStats',
    () => dashboardApi.getStats().then(res => res.data),
    {
      refetchInterval: 60000, // Refresh every minute
      staleTime: 30000, // Consider stale after 30 seconds
    }
  )
}

// Complete Dashboard Data Hook
export function useDashboardData() {
  return useQuery(
    'dashboardData',
    () => dashboardApi.getDashboardData().then(res => res.data),
    {
      refetchInterval: 60000, // Refresh every minute
      staleTime: 30000,
    }
  )
}

// Recent Activities Hook
export function useRecentActivities(limit: number = 20) {
  return useQuery(
    ['recentActivities', limit],
    () => dashboardApi.getRecentActivities(limit).then(res => res.data),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 15000,
    }
  )
}

// System Health Hook (Admin only)
export function useSystemHealth() {
  return useQuery(
    'systemHealth',
    () => dashboardApi.getSystemHealth().then(res => res.data),
    {
      refetchInterval: 30000,
      staleTime: 15000,
    }
  )
}

// System Configuration Hook (Admin only)
export function useSystemConfiguration() {
  return useQuery(
    'systemConfiguration',
    () => dashboardApi.getSystemConfiguration().then(res => res.data),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes - config doesn't change often
    }
  )
}