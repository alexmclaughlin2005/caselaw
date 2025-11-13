/**
 * TypeScript types for Data Management
 */

export interface DatasetInfo {
  key: string
  date: string
  type: 'schema' | 'csv' | 'script' | 'other'
  table_name?: string | null
  size: number
  last_modified: string
}

export interface AvailableDatasetsResponse {
  datasets: DatasetInfo[]
  dates: string[]
}

export interface DownloadRequest {
  date: string
  tables?: string[] | null
  include_schema?: boolean
}

export interface DownloadStatus {
  status: 'pending' | 'downloading' | 'completed' | 'failed'
  date: string
  files: Record<string, any>
  progress: number
  error?: string | null
  started_at?: string | null
  completed_at?: string | null
}

export interface ImportRequest {
  date: string
  tables?: string[] | null
}

export interface ImportStatus {
  status: 'pending' | 'importing' | 'completed' | 'failed'
  date: string
  current_table?: string | null
  tables_completed: string[]
  tables_total: number
  progress: number
  error?: string | null
  started_at?: string | null
  completed_at?: string | null
  records_imported?: Record<string, number>
}

export interface DatabaseStatus {
  // People database
  total_people: number
  total_positions: number
  total_schools: number
  total_educations: number

  // Case law database
  total_dockets: number
  total_opinion_clusters: number
  total_citations: number
  total_parentheticals: number

  last_import_date?: string | null
  last_import_status?: string | null
  database_size_mb?: number | null
}

export interface TableImportProgress {
  table_name: string
  current_count: number
  expected_count: number
  status: 'pending' | 'importing' | 'completed'
  progress_percent: number
}

export interface ImportProgressResponse {
  search_docket: TableImportProgress
  search_opinioncluster: TableImportProgress
  search_opinionscited: TableImportProgress
  search_parenthetical: TableImportProgress
}

