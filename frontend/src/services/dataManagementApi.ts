/**
 * Data Management API Client
 * 
 * API calls for data download, import, and status management.
 */
import apiClient from './api'
import type {
  AvailableDatasetsResponse,
  DatasetInfo,
  DownloadRequest,
  DownloadStatus,
  ImportRequest,
  ImportStatus,
  DatabaseStatus,
  ImportProgressResponse
} from '../types/dataManagement'

export const dataManagementApi = {
  /**
   * List all available datasets in S3
   */
  listDatasets: async (): Promise<AvailableDatasetsResponse> => {
    const response = await apiClient.get('/api/data/datasets')
    return response.data
  },

  /**
   * Get files for a specific date
   */
  getDatasetsForDate: async (date: string): Promise<DatasetInfo[]> => {
    const response = await apiClient.get(`/api/data/datasets/${date}`)
    return response.data
  },

  /**
   * Start downloading a dataset
   */
  startDownload: async (request: DownloadRequest): Promise<DownloadStatus> => {
    const response = await apiClient.post('/api/data/download', request)
    return response.data
  },

  /**
   * Get download status for a date
   */
  getDownloadStatus: async (date: string): Promise<DownloadStatus> => {
    const response = await apiClient.get(`/api/data/download/status/${date}`)
    return response.data
  },

  /**
   * Start importing a dataset
   */
  startImport: async (request: ImportRequest): Promise<ImportStatus> => {
    const response = await apiClient.post('/api/data/import', request)
    return response.data
  },

  /**
   * Get import status for a date
   */
  getImportStatus: async (date: string): Promise<ImportStatus> => {
    const response = await apiClient.get(`/api/data/import/status/${date}`)
    return response.data
  },

  /**
   * Get database status
   */
  getDatabaseStatus: async (): Promise<DatabaseStatus> => {
    const response = await apiClient.get('/api/data/status')
    return response.data
  },

  /**
   * Get real-time import progress for case law tables
   */
  getImportProgress: async (): Promise<ImportProgressResponse> => {
    const response = await apiClient.get('/api/data/import-progress')
    return response.data
  },
}

