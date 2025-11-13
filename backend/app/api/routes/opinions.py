"""
Opinion Cluster API Routes

Endpoints for searching and browsing opinion clusters.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, select
from typing import Optional, List
import logging

from app.api.deps import get_db
from app.models import OpinionCluster, Docket, Citation
from app.schemas.opinion import (
    OpinionClusterListItem,
    OpinionClusterDetail,
    OpinionSearchRequest,
    OpinionSearchResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=OpinionSearchResponse)
async def list_opinions(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query"),
    court_id: Optional[str] = Query(None, description="Filter by court ID (via docket)"),
    date_filed_after: Optional[str] = Query(None, description="Filter by date filed (YYYY-MM-DD)"),
    date_filed_before: Optional[str] = Query(None, description="Filter by date filed (YYYY-MM-DD)"),
    precedential_status: Optional[str] = Query(None, description="Filter by precedential status"),
    citation_count_min: Optional[int] = Query(None, description="Minimum citation count"),
    blocked: Optional[bool] = Query(None, description="Filter by blocked status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("date_filed", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
):
    """
    List and search opinion clusters with filtering and pagination.

    Supports:
    - Full-text search on case name, judges
    - Filtering by court, date, precedential status, citation count
    - Sorting by various fields
    - Pagination
    """
    try:
        # Build base query with join to docket for court filtering
        query = db.query(OpinionCluster)

        # Apply filters
        if q:
            # Full-text search on case name and judges
            search_filter = or_(
                OpinionCluster.case_name.ilike(f"%{q}%"),
                OpinionCluster.case_name_short.ilike(f"%{q}%"),
                OpinionCluster.case_name_full.ilike(f"%{q}%"),
                OpinionCluster.judges.ilike(f"%{q}%")
            )
            query = query.filter(search_filter)

        if court_id:
            # Join with docket to filter by court
            query = query.join(Docket).filter(Docket.court_id == court_id)

        if date_filed_after:
            query = query.filter(OpinionCluster.date_filed >= date_filed_after)

        if date_filed_before:
            query = query.filter(OpinionCluster.date_filed <= date_filed_before)

        if precedential_status:
            query = query.filter(OpinionCluster.precedential_status == precedential_status)

        if citation_count_min is not None:
            query = query.filter(OpinionCluster.citation_count >= citation_count_min)

        if blocked is not None:
            query = query.filter(OpinionCluster.blocked == blocked)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(OpinionCluster, sort_by, OpinionCluster.date_filed)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        opinions = query.all()

        # Convert to response models
        items = [OpinionClusterListItem.model_validate(op) for op in opinions]

        # Calculate pagination metadata
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        return OpinionSearchResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    except Exception as e:
        logger.error(f"Error listing opinions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing opinions: {str(e)}")


@router.get("/{opinion_id}", response_model=OpinionClusterDetail)
async def get_opinion(
    opinion_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific opinion cluster.

    Args:
        opinion_id: The ID of the opinion cluster to retrieve
    """
    try:
        opinion = db.query(OpinionCluster).filter(OpinionCluster.id == opinion_id).first()

        if not opinion:
            raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

        return OpinionClusterDetail.model_validate(opinion)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opinion {opinion_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving opinion: {str(e)}")


@router.get("/{opinion_id}/docket")
async def get_opinion_docket(
    opinion_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the docket associated with an opinion cluster.

    Args:
        opinion_id: The ID of the opinion cluster
    """
    try:
        opinion = db.query(OpinionCluster).filter(OpinionCluster.id == opinion_id).first()
        if not opinion:
            raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

        docket = db.query(Docket).filter(Docket.id == opinion.docket_id).first()
        if not docket:
            raise HTTPException(status_code=404, detail=f"Docket not found for opinion {opinion_id}")

        return {
            "docket_id": docket.id,
            "docket_number": docket.docket_number,
            "case_name": docket.case_name,
            "court_id": docket.court_id,
            "date_filed": docket.date_filed,
            "assigned_to_str": docket.assigned_to_str,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting docket for opinion {opinion_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving docket: {str(e)}")


@router.get("/stats/top-cited")
async def get_top_cited_opinions(
    db: Session = Depends(get_db),
    court_id: Optional[str] = Query(None, description="Filter by court"),
    limit: int = Query(100, ge=1, le=500, description="Number of opinions to return"),
):
    """
    Get the most cited opinion clusters.

    Returns opinions ordered by citation count.
    """
    try:
        query = db.query(
            OpinionCluster.id,
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.citation_count,
            OpinionCluster.precedential_status,
            Docket.court_id
        ).join(Docket).filter(
            OpinionCluster.citation_count > 0
        )

        if court_id:
            query = query.filter(Docket.court_id == court_id)

        query = query.order_by(OpinionCluster.citation_count.desc()).limit(limit)

        results = query.all()

        return {
            "opinions": [
                {
                    "id": r.id,
                    "case_name": r.case_name,
                    "date_filed": str(r.date_filed) if r.date_filed else None,
                    "citation_count": r.citation_count,
                    "precedential_status": r.precedential_status,
                    "court_id": r.court_id,
                }
                for r in results
            ],
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"Error getting top cited opinions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting top cited opinions: {str(e)}")


@router.get("/stats/by-status")
async def get_opinions_by_status(
    db: Session = Depends(get_db),
):
    """
    Get opinion counts grouped by precedential status.
    """
    try:
        results = db.query(
            OpinionCluster.precedential_status,
            func.count(OpinionCluster.id).label('count')
        ).filter(
            OpinionCluster.precedential_status.isnot(None)
        ).group_by(
            OpinionCluster.precedential_status
        ).order_by(
            func.count(OpinionCluster.id).desc()
        ).all()

        return {
            "statuses": [
                {
                    "status": r.precedential_status,
                    "count": r.count
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Error getting opinions by status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting status statistics: {str(e)}")


@router.get("/stats/timeline")
async def get_opinion_timeline(
    db: Session = Depends(get_db),
    court_id: Optional[str] = Query(None, description="Filter by court"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get timeline data for opinions filed over time.

    Returns aggregated counts by year.
    """
    try:
        # Build query to aggregate by year
        query = db.query(
            func.extract('year', OpinionCluster.date_filed).label('year'),
            func.count(OpinionCluster.id).label('count')
        ).filter(OpinionCluster.date_filed.isnot(None))

        # Apply filters
        if court_id:
            query = query.join(Docket).filter(Docket.court_id == court_id)

        if start_year:
            query = query.filter(func.extract('year', OpinionCluster.date_filed) >= start_year)

        if end_year:
            query = query.filter(func.extract('year', OpinionCluster.date_filed) <= end_year)

        # Group and order
        query = query.group_by('year').order_by('year')

        results = query.all()

        return {
            "timeline": [
                {
                    "year": int(r.year),
                    "count": r.count
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Error getting opinion timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")
