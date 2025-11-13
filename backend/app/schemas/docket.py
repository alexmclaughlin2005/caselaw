"""
Pydantic schemas for Docket API responses and requests
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class DocketBase(BaseModel):
    """Base schema for Docket"""
    docket_number: Optional[str] = None
    case_name: Optional[str] = None
    case_name_short: Optional[str] = None
    case_name_full: Optional[str] = None
    date_filed: Optional[date] = None
    date_terminated: Optional[date] = None
    court_id: Optional[str] = None
    nature_of_suit: Optional[str] = None
    cause: Optional[str] = None

    class Config:
        from_attributes = True


class DocketListItem(DocketBase):
    """Schema for docket list items (minimal fields for browsing)"""
    id: int
    assigned_to_str: Optional[str] = None
    blocked: Optional[bool] = False
    view_count: Optional[int] = 0

    # Computed fields
    opinion_count: Optional[int] = Field(default=0, description="Number of opinions in this docket")


class DocketDetail(DocketBase):
    """Schema for detailed docket view"""
    id: int

    # Foreign keys
    assigned_to_id: Optional[int] = None
    referred_to_id: Optional[int] = None
    appeal_from_id: Optional[str] = None

    # String representations
    assigned_to_str: Optional[str] = None
    referred_to_str: Optional[str] = None
    appeal_from_str: Optional[str] = None
    panel_str: Optional[str] = None

    # Additional dates
    date_argued: Optional[date] = None
    date_reargued: Optional[date] = None
    date_cert_granted: Optional[date] = None
    date_cert_denied: Optional[date] = None
    date_last_filing: Optional[date] = None

    # Case details
    jurisdiction_type: Optional[str] = None
    jury_demand: Optional[str] = None
    pacer_case_id: Optional[str] = None
    slug: Optional[str] = None
    blocked: Optional[bool] = False

    # Federal docket number breakdown
    docket_number_core: Optional[str] = None
    federal_dn_case_type: Optional[str] = None
    federal_dn_judge_initials_assigned: Optional[str] = None
    federal_dn_office_code: Optional[str] = None

    # MDL and metadata
    mdl_status: Optional[str] = None
    view_count: Optional[int] = None

    # Timestamps
    date_created: Optional[datetime] = None
    date_modified: Optional[datetime] = None


class DocketSearchRequest(BaseModel):
    """Schema for docket search requests"""
    q: Optional[str] = Field(None, description="Full-text search query")
    court_id: Optional[List[str]] = Field(None, description="Filter by court IDs")
    date_filed_after: Optional[date] = Field(None, description="Filed on or after this date")
    date_filed_before: Optional[date] = Field(None, description="Filed on or before this date")
    assigned_to_id: Optional[int] = Field(None, description="Filter by assigned judge ID")
    nature_of_suit: Optional[str] = Field(None, description="Filter by nature of suit")
    blocked: Optional[bool] = Field(None, description="Filter by blocked status")
    has_opinions: Optional[bool] = Field(None, description="Only dockets with opinions")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field("date_filed", description="Field to sort by")
    sort_order: str = Field("desc", description="Sort order: asc or desc")


class DocketSearchResponse(BaseModel):
    """Schema for paginated docket search results"""
    items: List[DocketListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
