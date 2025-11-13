"""
Pydantic schemas for Citation API responses and requests
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class CitationBase(BaseModel):
    """Base schema for Citation"""
    citing_opinion_id: int
    cited_opinion_id: int
    depth: Optional[int] = 0

    class Config:
        from_attributes = True


class CitationListItem(CitationBase):
    """Schema for citation list items with opinion details"""
    id: int

    # Include basic opinion info for the cited/citing opinion
    cited_case_name: Optional[str] = None
    cited_date_filed: Optional[str] = None
    cited_citation_count: Optional[int] = 0

    citing_case_name: Optional[str] = None
    citing_date_filed: Optional[str] = None


class CitationNetworkNode(BaseModel):
    """Schema for a node in the citation network"""
    id: int
    opinion_id: int
    case_name: str
    date_filed: Optional[str] = None
    citation_count: int = 0
    precedential_status: Optional[str] = None


class CitationNetworkEdge(BaseModel):
    """Schema for an edge in the citation network"""
    source: int  # opinion_id
    target: int  # opinion_id
    depth: Optional[int] = 0


class CitationNetworkResponse(BaseModel):
    """Schema for citation network graph data"""
    nodes: List[CitationNetworkNode]
    edges: List[CitationNetworkEdge]
    center_opinion_id: int
    max_depth: int = Field(default=2, description="Maximum depth explored")


class CitationStatsResponse(BaseModel):
    """Schema for citation statistics"""
    opinion_id: int
    case_name: str

    # Citation counts
    times_cited: int = Field(description="Number of times this opinion is cited")
    times_citing: int = Field(description="Number of opinions this opinion cites")

    # Top citing/cited cases
    top_citing_cases: List[CitationListItem] = Field(description="Top cases citing this opinion")
    top_cited_cases: List[CitationListItem] = Field(description="Top cases cited by this opinion")


class TopCitedOpinionsResponse(BaseModel):
    """Schema for most cited opinions"""
    items: List[dict]  # opinion_id, case_name, citation_count, court_id
    total: int
    page: int
    page_size: int
