"""
Docket API Routes

Endpoints for searching and browsing dockets (cases).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, select
from typing import Optional, List
import logging

from app.api.deps import get_db
from app.models import Docket, OpinionCluster, Court
from app.schemas.docket import (
    DocketListItem,
    DocketDetail,
    DocketSearchRequest,
    DocketSearchResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=DocketSearchResponse)
async def list_dockets(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query"),
    court_id: Optional[str] = Query(None, description="Filter by court ID"),
    date_filed_after: Optional[str] = Query(None, description="Filter by date filed (YYYY-MM-DD)"),
    date_filed_before: Optional[str] = Query(None, description="Filter by date filed (YYYY-MM-DD)"),
    assigned_to_id: Optional[int] = Query(None, description="Filter by assigned judge ID"),
    blocked: Optional[bool] = Query(None, description="Filter by blocked status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("date_filed", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
):
    """
    List and search dockets with filtering and pagination.

    Supports:
    - Full-text search on case name
    - Filtering by court, date, judge, blocked status
    - Sorting by various fields
    - Pagination
    """
    try:
        # Build base query
        query = db.query(Docket)

        # Apply filters
        if q:
            # Full-text search on case name fields
            search_filter = or_(
                Docket.case_name.ilike(f"%{q}%"),
                Docket.case_name_short.ilike(f"%{q}%"),
                Docket.case_name_full.ilike(f"%{q}%"),
                Docket.docket_number.ilike(f"%{q}%")
            )
            query = query.filter(search_filter)

        if court_id:
            query = query.filter(Docket.court_id == court_id)

        if date_filed_after:
            query = query.filter(Docket.date_filed >= date_filed_after)

        if date_filed_before:
            query = query.filter(Docket.date_filed <= date_filed_before)

        if assigned_to_id is not None:
            query = query.filter(Docket.assigned_to_id == assigned_to_id)

        if blocked is not None:
            query = query.filter(Docket.blocked == blocked)

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        sort_column = getattr(Docket, sort_by, Docket.date_filed)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        dockets = query.all()

        # Convert to response models
        items = []
        for docket in dockets:
            # Get opinion count for this docket
            opinion_count = db.query(func.count(OpinionCluster.id)).filter(
                OpinionCluster.docket_id == docket.id
            ).scalar() or 0

            item = DocketListItem.model_validate(docket)
            item.opinion_count = opinion_count
            items.append(item)

        # Calculate pagination metadata
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1

        return DocketSearchResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
        )

    except Exception as e:
        logger.error(f"Error listing dockets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing dockets: {str(e)}")


@router.get("/{docket_id}", response_model=DocketDetail)
async def get_docket(
    docket_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific docket.

    Args:
        docket_id: The ID of the docket to retrieve
    """
    try:
        docket = db.query(Docket).filter(Docket.id == docket_id).first()

        if not docket:
            raise HTTPException(status_code=404, detail=f"Docket {docket_id} not found")

        return DocketDetail.model_validate(docket)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting docket {docket_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving docket: {str(e)}")


@router.get("/{docket_id}/opinions")
async def get_docket_opinions(
    docket_id: int,
    db: Session = Depends(get_db),
):
    """
    Get all opinion clusters associated with a docket.

    Args:
        docket_id: The ID of the docket
    """
    try:
        # Verify docket exists
        docket = db.query(Docket).filter(Docket.id == docket_id).first()
        if not docket:
            raise HTTPException(status_code=404, detail=f"Docket {docket_id} not found")

        # Get all opinions for this docket
        opinions = db.query(OpinionCluster).filter(
            OpinionCluster.docket_id == docket_id
        ).order_by(OpinionCluster.date_filed.desc()).all()

        return {
            "docket_id": docket_id,
            "case_name": docket.case_name,
            "opinion_count": len(opinions),
            "opinions": [
                {
                    "id": op.id,
                    "case_name": op.case_name,
                    "date_filed": op.date_filed,
                    "judges": op.judges,
                    "precedential_status": op.precedential_status,
                    "citation_count": op.citation_count,
                    "slug": op.slug,
                }
                for op in opinions
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opinions for docket {docket_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving opinions: {str(e)}")


@router.get("/stats/timeline")
async def get_docket_timeline(
    db: Session = Depends(get_db),
    court_id: Optional[str] = Query(None, description="Filter by court"),
    start_year: Optional[int] = Query(None, description="Start year"),
    end_year: Optional[int] = Query(None, description="End year"),
):
    """
    Get timeline data for dockets filed over time.

    Returns aggregated counts by year and month.
    """
    try:
        # Build query to aggregate by year and month
        query = db.query(
            func.extract('year', Docket.date_filed).label('year'),
            func.extract('month', Docket.date_filed).label('month'),
            func.count(Docket.id).label('count')
        ).filter(Docket.date_filed.isnot(None))

        # Apply filters
        if court_id:
            query = query.filter(Docket.court_id == court_id)

        if start_year:
            query = query.filter(func.extract('year', Docket.date_filed) >= start_year)

        if end_year:
            query = query.filter(func.extract('year', Docket.date_filed) <= end_year)

        # Group and order
        query = query.group_by('year', 'month').order_by('year', 'month')

        results = query.all()

        return {
            "timeline": [
                {
                    "year": int(r.year),
                    "month": int(r.month),
                    "count": r.count
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Error getting docket timeline: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting timeline: {str(e)}")


@router.get("/stats/by-court")
async def get_dockets_by_court(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Number of courts to return"),
):
    """
    Get docket counts grouped by court.

    Returns the top courts by number of dockets.
    """
    try:
        results = db.query(
            Docket.court_id,
            func.count(Docket.id).label('docket_count')
        ).filter(
            Docket.court_id.isnot(None)
        ).group_by(
            Docket.court_id
        ).order_by(
            func.count(Docket.id).desc()
        ).limit(limit).all()

        # Get court names
        court_ids = [r.court_id for r in results]
        courts = db.query(Court).filter(Court.id.in_(court_ids)).all()
        court_map = {c.id: c.full_name or c.short_name for c in courts}

        return {
            "courts": [
                {
                    "court_id": r.court_id,
                    "court_name": court_map.get(r.court_id, r.court_id),
                    "docket_count": r.docket_count
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Error getting dockets by court: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting court statistics: {str(e)}")
