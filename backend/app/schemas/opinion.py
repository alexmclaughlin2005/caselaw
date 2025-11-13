"""
Pydantic schemas for Opinion Cluster API responses and requests
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class OpinionClusterBase(BaseModel):
    """Base schema for Opinion Cluster"""
    case_name: Optional[str] = None
    case_name_short: Optional[str] = None
    case_name_full: Optional[str] = None
    date_filed: Optional[date] = None
    judges: Optional[str] = None
    precedential_status: Optional[str] = None
    citation_count: Optional[int] = 0

    class Config:
        from_attributes = True


class OpinionClusterListItem(OpinionClusterBase):
    """Schema for opinion cluster list items"""
    id: int
    docket_id: int
    slug: Optional[str] = None
    blocked: Optional[bool] = False
    source: Optional[str] = None

    # SCDB fields for Supreme Court cases
    scdb_id: Optional[str] = None
    scdb_decision_direction: Optional[str] = None


class OpinionClusterDetail(OpinionClusterBase):
    """Schema for detailed opinion cluster view"""
    id: int
    docket_id: int

    # Additional dates
    date_argued: Optional[date] = None
    date_reargued: Optional[date] = None
    date_reargument_denied: Optional[date] = None

    # Full metadata
    attorneys: Optional[str] = None
    nature_of_suit: Optional[str] = None
    posture: Optional[str] = None
    syllabus: Optional[str] = None
    headnotes: Optional[str] = None
    summary: Optional[str] = None

    # Source and identifiers
    source: Optional[str] = None
    slug: Optional[str] = None
    blocked: Optional[bool] = False

    # SCDB fields (Supreme Court Database)
    scdb_id: Optional[str] = None
    scdb_decision_direction: Optional[str] = None
    scdb_votes_majority: Optional[int] = None
    scdb_votes_minority: Optional[int] = None


class OpinionSearchRequest(BaseModel):
    """Schema for opinion search requests"""
    q: Optional[str] = Field(None, description="Full-text search query (case name, judges)")
    court_id: Optional[List[str]] = Field(None, description="Filter by court IDs (via docket)")
    date_filed_after: Optional[date] = Field(None, description="Filed on or after this date")
    date_filed_before: Optional[date] = Field(None, description="Filed on or before this date")
    precedential_status: Optional[List[str]] = Field(None, description="Filter by precedential status")
    citation_count_min: Optional[int] = Field(None, description="Minimum citation count")
    judge_name: Optional[str] = Field(None, description="Filter by judge name")
    scdb_decision_direction: Optional[str] = Field(None, description="SCDB decision direction")
    blocked: Optional[bool] = Field(None, description="Filter by blocked status")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field("date_filed", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order: asc or desc")


class OpinionSearchResponse(BaseModel):
    """Schema for paginated opinion search results"""
    items: List[OpinionClusterListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
