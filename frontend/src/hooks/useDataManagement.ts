/**
 * Custom hooks for Data Management
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dataManagementApi } from '../services/dataManagementApi'
import type { DownloadRequest, ImportRequest } from '../types/dataManagement'

/**
 * Hook to fetch available datasets
 */
export const useDatasets = () => {
  return useQuery({
    queryKey: ['datasets'],
    queryFn: () => dataManagementApi.listDatasets(),
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

/**
 * Hook to fetch datasets for a specific date
 */
export const useDatasetsForDate = (date: string) => {
  return useQuery({
    queryKey: ['datasets', date],
    queryFn: () => dataManagementApi.getDatasetsForDate(date),
    enabled: !!date,
  })
}

/**
 * Hook to fetch download status
 */
export const useDownloadStatus = (date: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['download-status', date],
    queryFn: () => dataManagementApi.getDownloadStatus(date),
    enabled: enabled && !!date,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      // Poll more frequently if downloading
      if (status === 'downloading' || status === 'pending') {
        return 2000 // 2 seconds
      }
      return false // Don't poll if completed or failed
    },
  })
}

/**
 * Hook to start a download
 */
export const useStartDownload = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: DownloadRequest) => dataManagementApi.startDownload(request),
    onSuccess: (_data, variables) => {
      // Invalidate download status query
      queryClient.invalidateQueries({ queryKey: ['download-status', variables.date] })
      // Invalidate datasets query
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}

/**
 * Hook to fetch import status
 */
export const useImportStatus = (date: string, enabled: boolean = true) => {
  return useQuery({
    queryKey: ['import-status', date],
    queryFn: () => dataManagementApi.getImportStatus(date),
    enabled: enabled && !!date,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      // Poll more frequently if importing
      if (status === 'importing' || status === 'pending') {
        return 2000 // 2 seconds
      }
      return false // Don't poll if completed or failed
    },
  })
}

/**
 * Hook to start an import
 */
export const useStartImport = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ImportRequest) => dataManagementApi.startImport(request),
    onSuccess: (_data, variables) => {
      // Invalidate import status query
      queryClient.invalidateQueries({ queryKey: ['import-status', variables.date] })
      // Invalidate database status
      queryClient.invalidateQueries({ queryKey: ['database-status'] })
    },
  })
}

/**
 * Hook to fetch database status
 */
export const useDatabaseStatus = () => {
  return useQuery({
    queryKey: ['database-status'],
    queryFn: () => dataManagementApi.getDatabaseStatus(),
    refetchInterval: 10000, // Refetch every 10 seconds
  })
}

/**
 * Hook to fetch import progress (manual refresh)
 */
export const useImportProgress = () => {
  return useQuery({
    queryKey: ['import-progress'],
    queryFn: () => dataManagementApi.getImportProgress(),
    refetchOnWindowFocus: false, // Don't auto-refetch on window focus
    staleTime: Infinity, // Data never goes stale, only refresh manually
  })
}

