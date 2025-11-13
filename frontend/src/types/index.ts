/**
 * TypeScript Type Definitions
 * 
 * Central location for shared TypeScript types and interfaces.
 */

// API Response types
export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    total: number
    page: number
    page_size: number
    has_next: boolean
    has_prev: boolean
  }
}

// Person types (will be expanded as we build models)
export interface Person {
  id: number
  name_first?: string
  name_middle?: string
  name_last?: string
  name_suffix?: string
  date_dob?: string
  date_dod?: string
}

// Position types
export interface Position {
  id: number
  person_id: number
  court_id?: number
  position_type?: string
  date_start?: string
  date_termination?: string
}

// School types
export interface School {
  id: number
  name: string
}

// Court types
export interface Court {
  id: number
  name: string
  jurisdiction?: string
}

