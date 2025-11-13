/**
 * Docket API Service
 *
 * API functions for docket search and retrieval
 */
import apiClient from './api'

export interface DocketListItem {
  id: number
  docket_number: string | null
  case_name: string | null
  case_name_short: string | null
  case_name_full: string | null
  date_filed: string | null
  date_terminated: string | null
  court_id: string | null
  nature_of_suit: string | null
  cause: string | null
  assigned_to_str: string | null
  blocked: boolean
  view_count: number
  opinion_count: number
}

export interface DocketSearchParams {
  q?: string
  court_id?: string
  date_filed_after?: string
  date_filed_before?: string
  assigned_to_id?: number
  blocked?: boolean
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface DocketSearchResponse {
  items: DocketListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface DocketDetail extends DocketListItem {
  assigned_to_id: number | null
  referred_to_id: number | null
  appeal_from_id: string | null
  referred_to_str: string | null
  appeal_from_str: string | null
  panel_str: string | null
  date_argued: string | null
  date_reargued: string | null
  date_cert_granted: string | null
  date_cert_denied: string | null
  date_last_filing: string | null
  jurisdiction_type: string | null
  jury_demand: string | null
  pacer_case_id: string | null
  slug: string | null
  docket_number_core: string | null
  federal_dn_case_type: string | null
  federal_dn_judge_initials_assigned: string | null
  federal_dn_office_code: string | null
  mdl_status: string | null
  date_created: string | null
  date_modified: string | null
}

/**
 * Search and list dockets
 */
export const searchDockets = async (params: DocketSearchParams = {}): Promise<DocketSearchResponse> => {
  const response = await apiClient.get('/api/dockets/', { params })
  return response.data
}

/**
 * Get a single docket by ID
 */
export const getDocket = async (docketId: number): Promise<DocketDetail> => {
  const response = await apiClient.get(`/api/dockets/${docketId}`)
  return response.data
}

/**
 * Get opinions for a docket
 */
export const getDocketOpinions = async (docketId: number) => {
  const response = await apiClient.get(`/api/dockets/${docketId}/opinions`)
  return response.data
}

/**
 * Get docket timeline statistics
 */
export const getDocketTimeline = async (params: {
  court_id?: string
  start_year?: number
  end_year?: number
}) => {
  const response = await apiClient.get('/api/dockets/stats/timeline', { params })
  return response.data
}

/**
 * Get dockets by court statistics
 */
export const getDocketsByCourt = async (limit: number = 50) => {
  const response = await apiClient.get('/api/dockets/stats/by-court', { params: { limit } })
  return response.data
}
