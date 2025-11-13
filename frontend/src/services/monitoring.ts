/**
 * Monitoring API Service
 *
 * API functions for monitoring database import progress and system status
 */
import apiClient from './api'

export interface TableProgress {
  current: number
  expected: number
  percentage: number
  remaining: number
  status: 'pending' | 'importing' | 'completed'
}

export interface ImportProgress {
  tables: {
    [key: string]: TableProgress
  }
  overall: {
    current: number
    expected: number
    percentage: number
    remaining: number
  }
}

export interface DatabaseCounts {
  counts: {
    [key: string]: number
  }
  database_size: string
  table_sizes: {
    [key: string]: string
  }
  total_records: number
}

export interface DatabaseActivity {
  connection_count: number
  active_queries: number
  idle_connections: number
  active_query_details: Array<{
    pid: number
    query: string
    state: string
    duration_seconds: number
  }>
}

/**
 * Get import progress for all tables
 */
export const getImportProgress = async (): Promise<ImportProgress> => {
  const response = await apiClient.get('/api/monitoring/import/progress')
  return response.data
}

/**
 * Get current database record counts
 */
export const getDatabaseCounts = async (): Promise<DatabaseCounts> => {
  const response = await apiClient.get('/api/monitoring/database/counts')
  return response.data
}

/**
 * Get current database activity
 */
export const getDatabaseActivity = async (): Promise<DatabaseActivity> => {
  const response = await apiClient.get('/api/monitoring/database/activity')
  return response.data
}
