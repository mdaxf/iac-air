import { useQuery, useMutation, useQueryClient } from 'react-query'
import { apiHistoryApi } from '@/services/api'
import type {
  APIHistoryRecord,
  APIHistoryStats,
  APIHistoryFilter,
  APIHistoryResponse,
  APIHistoryDetailRecord
} from '@/types'

// API History hooks
export function useAPIHistory(
  offset: number = 0,
  limit: number = 50,
  filters: Partial<APIHistoryFilter> = {}
) {
  // Clean filters: remove empty strings and convert them to undefined
  const cleanFilters = Object.fromEntries(
    Object.entries(filters).filter(([key, value]) => {
      // Remove empty strings, null, and undefined values
      return value !== '' && value !== null && value !== undefined
    })
  ) as Partial<APIHistoryFilter>

  return useQuery(
    ['apiHistory', offset, limit, cleanFilters],
    () => apiHistoryApi.getHistory({ offset, limit, ...cleanFilters }).then(res => res.data),
    {
      keepPreviousData: true,
      staleTime: 30000, // 30 seconds
    }
  )
}

export function useAPIHistoryDetail(recordId: string) {
  return useQuery(
    ['apiHistoryDetail', recordId],
    () => apiHistoryApi.getHistoryDetail(recordId).then(res => res.data),
    {
      enabled: !!recordId,
    }
  )
}

export function useAPIHistoryStats(hours: number = 24) {
  return useQuery(
    ['apiHistoryStats', hours],
    () => apiHistoryApi.getStats(hours).then(res => res.data),
    {
      refetchInterval: 60000, // Refresh every minute
      staleTime: 30000,
    }
  )
}

export function useDeleteAPIHistory() {
  const queryClient = useQueryClient()
  return useMutation(
    (recordId: string) => apiHistoryApi.deleteRecord(recordId).then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('apiHistory')
      },
    }
  )
}

export function useCleanupAPIHistory() {
  const queryClient = useQueryClient()
  return useMutation(
    () => apiHistoryApi.cleanup().then(res => res.data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('apiHistory')
        queryClient.invalidateQueries('apiHistoryStats')
      },
    }
  )
}

export function useAPIHistoryConfig() {
  return useQuery(
    'apiHistoryConfig',
    () => apiHistoryApi.getConfig().then(res => res.data),
    {
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  )
}

export function useExportAPIHistory() {
  return useMutation(
    (params: {
      start_date?: string
      end_date?: string
      method?: string
      status_range?: string
    }) => apiHistoryApi.exportCSV(params)
  )
}