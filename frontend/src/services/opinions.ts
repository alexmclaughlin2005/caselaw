/**
 * Opinion API Service
 *
 * API functions for opinion cluster search and retrieval
 */
import apiClient from './api'

export interface OpinionListItem {
  id: number
  docket_id: number
  case_name: string | null
  case_name_short: string | null
  case_name_full: string | null
  date_filed: string | null
  judges: string | null
  precedential_status: string | null
  citation_count: number
  slug: string | null
  blocked: boolean
  source: string | null
  scdb_id: string | null
  scdb_decision_direction: string | null
}

export interface OpinionSearchParams {
  q?: string
  court_id?: string
  date_filed_after?: string
  date_filed_before?: string
  precedential_status?: string
  citation_count_min?: number
  judge_name?: string
  blocked?: boolean
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface OpinionSearchResponse {
  items: OpinionListItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface OpinionDetail extends OpinionListItem {
  date_argued: string | null
  date_reargued: string | null
  date_reargument_denied: string | null
  attorneys: string | null
  nature_of_suit: string | null
  posture: string | null
  syllabus: string | null
  headnotes: string | null
  summary: string | null
  scdb_votes_majority: number | null
  scdb_votes_minority: number | null
}

/**
 * Search and list opinions
 */
export const searchOpinions = async (params: OpinionSearchParams = {}): Promise<OpinionSearchResponse> => {
  const response = await apiClient.get('/api/opinions/', { params })
  return response.data
}

/**
 * Get a single opinion by ID
 */
export const getOpinion = async (opinionId: number): Promise<OpinionDetail> => {
  const response = await apiClient.get(`/api/opinions/${opinionId}`)
  return response.data
}

/**
 * Get the docket for an opinion
 */
export const getOpinionDocket = async (opinionId: number) => {
  const response = await apiClient.get(`/api/opinions/${opinionId}/docket`)
  return response.data
}

/**
 * Get top cited opinions
 */
export const getTopCitedOpinions = async (params: { court_id?: string; limit?: number }) => {
  const response = await apiClient.get('/api/opinions/stats/top-cited', { params })
  return response.data
}

/**
 * Get opinions by precedential status
 */
export const getOpinionsByStatus = async () => {
  const response = await apiClient.get('/api/opinions/stats/by-status')
  return response.data
}

/**
 * Get opinion timeline statistics
 */
export const getOpinionTimeline = async (params: {
  court_id?: string
  start_year?: number
  end_year?: number
}) => {
  const response = await apiClient.get('/api/opinions/stats/timeline', { params })
  return response.data
}
