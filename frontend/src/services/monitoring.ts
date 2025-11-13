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

export interface LiveTableStatus {
  current: number
  expected: number
  percentage: number
  status: 'pending' | 'importing' | 'completed'
}

export interface LiveImportStatus {
  import_status: 'not_started' | 'importing' | 'paused' | 'completed'
  overall_percentage: number
  total_records: number
  expected_total: number
  tables: {
    [key: string]: LiveTableStatus
  }
  active_queries: number
  query_details: Array<{
    pid: number
    query: string
    state: string
    duration: string
    table: string
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
 * Get live import status with all tables including people DB
 */
export const getLiveImportStatus = async (): Promise<LiveImportStatus> => {
  const response = await apiClient.get('/api/monitoring/import/live-status')
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
