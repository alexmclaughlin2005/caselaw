/**
 * Citation API Service
 *
 * API functions for citation network exploration
 */
import apiClient from './api'

export interface CitationNetworkNode {
  id: number
  opinion_id: number
  case_name: string
  date_filed: string | null
  citation_count: number
  precedential_status: string | null
}

export interface CitationNetworkEdge {
  source: number
  target: number
  depth: number
}

export interface CitationNetworkResponse {
  nodes: CitationNetworkNode[]
  edges: CitationNetworkEdge[]
  center_opinion_id: number
  max_depth: number
}

/**
 * Get opinions citing this opinion
 */
export const getCitingOpinions = async (opinionId: number, limit: number = 100) => {
  const response = await apiClient.get(`/api/citations/${opinionId}/citing`, { params: { limit } })
  return response.data
}

/**
 * Get opinions cited by this opinion
 */
export const getCitedOpinions = async (opinionId: number, limit: number = 100) => {
  const response = await apiClient.get(`/api/citations/${opinionId}/cited`, { params: { limit } })
  return response.data
}

/**
 * Get citation statistics for an opinion
 */
export const getCitationStats = async (opinionId: number) => {
  const response = await apiClient.get(`/api/citations/${opinionId}/stats`)
  return response.data
}

/**
 * Get citation network graph data
 */
export const getCitationNetwork = async (
  opinionId: number,
  maxDepth: number = 2,
  maxNodes: number = 100
): Promise<CitationNetworkResponse> => {
  const response = await apiClient.get(`/api/citations/${opinionId}/network`, {
    params: { max_depth: maxDepth, max_nodes: maxNodes }
  })
  return response.data
}

/**
 * Get most cited cases
 */
export const getMostCitedCases = async (limit: number = 100) => {
  const response = await apiClient.get('/api/citations/stats/most-cited', { params: { limit } })
  return response.data
}
