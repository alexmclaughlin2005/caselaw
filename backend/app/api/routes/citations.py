"""
Citation API Routes

Endpoints for exploring citation networks and relationships between cases.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import Optional, List, Dict, Set
import logging

from app.api.deps import get_db
from app.models import Citation, OpinionCluster, Docket
from app.schemas.citation import (
    CitationListItem,
    CitationNetworkNode,
    CitationNetworkEdge,
    CitationNetworkResponse,
    CitationStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{opinion_id}/citing")
async def get_citing_opinions(
    opinion_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
):
    """
    Get opinions that cite this opinion.

    Args:
        opinion_id: The opinion being cited
    """
    try:
        # Verify opinion exists
        opinion = db.query(OpinionCluster).filter(OpinionCluster.id == opinion_id).first()
        if not opinion:
            raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

        # Get citations where this opinion is cited
        results = db.query(
            Citation.id,
            Citation.citing_opinion_id,
            Citation.cited_opinion_id,
            Citation.depth,
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.citation_count
        ).join(
            OpinionCluster,
            Citation.citing_opinion_id == OpinionCluster.id
        ).filter(
            Citation.cited_opinion_id == opinion_id
        ).order_by(
            OpinionCluster.citation_count.desc()
        ).limit(limit).all()

        return {
            "opinion_id": opinion_id,
            "case_name": opinion.case_name,
            "times_cited": len(results),
            "citing_opinions": [
                {
                    "id": r.id,
                    "citing_opinion_id": r.citing_opinion_id,
                    "cited_opinion_id": r.cited_opinion_id,
                    "depth": r.depth,
                    "citing_case_name": r.case_name,
                    "citing_date_filed": str(r.date_filed) if r.date_filed else None,
                    "citing_citation_count": r.citation_count,
                }
                for r in results
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting citing opinions for {opinion_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving citing opinions: {str(e)}")


@router.get("/{opinion_id}/cited")
async def get_cited_opinions(
    opinion_id: int,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
):
    """
    Get opinions cited by this opinion.

    Args:
        opinion_id: The opinion that cites others
    """
    try:
        # Verify opinion exists
        opinion = db.query(OpinionCluster).filter(OpinionCluster.id == opinion_id).first()
        if not opinion:
            raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

        # Get citations where this opinion cites others
        results = db.query(
            Citation.id,
            Citation.citing_opinion_id,
            Citation.cited_opinion_id,
            Citation.depth,
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.citation_count
        ).join(
            OpinionCluster,
            Citation.cited_opinion_id == OpinionCluster.id
        ).filter(
            Citation.citing_opinion_id == opinion_id
        ).order_by(
            OpinionCluster.citation_count.desc()
        ).limit(limit).all()

        return {
            "opinion_id": opinion_id,
            "case_name": opinion.case_name,
            "times_citing": len(results),
            "cited_opinions": [
                {
                    "id": r.id,
                    "citing_opinion_id": r.citing_opinion_id,
                    "cited_opinion_id": r.cited_opinion_id,
                    "depth": r.depth,
                    "cited_case_name": r.case_name,
                    "cited_date_filed": str(r.date_filed) if r.date_filed else None,
                    "cited_citation_count": r.citation_count,
                }
                for r in results
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cited opinions for {opinion_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving cited opinions: {str(e)}")


@router.get("/{opinion_id}/stats")
async def get_citation_stats(
    opinion_id: int,
    db: Session = Depends(get_db),
):
    """
    Get citation statistics for an opinion.

    Returns counts and top citing/cited cases.
    """
    try:
        # Verify opinion exists
        opinion = db.query(OpinionCluster).filter(OpinionCluster.id == opinion_id).first()
        if not opinion:
            raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

        # Count citations (times this opinion is cited by others)
        times_cited = db.query(func.count(Citation.id)).filter(
            Citation.cited_opinion_id == opinion_id
        ).scalar() or 0

        # Count citations (times this opinion cites others)
        times_citing = db.query(func.count(Citation.id)).filter(
            Citation.citing_opinion_id == opinion_id
        ).scalar() or 0

        # Get top 10 cases citing this opinion
        top_citing = db.query(
            Citation.id,
            Citation.citing_opinion_id,
            Citation.cited_opinion_id,
            Citation.depth,
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.citation_count
        ).join(
            OpinionCluster,
            Citation.citing_opinion_id == OpinionCluster.id
        ).filter(
            Citation.cited_opinion_id == opinion_id
        ).order_by(
            OpinionCluster.citation_count.desc()
        ).limit(10).all()

        # Get top 10 cases cited by this opinion
        top_cited = db.query(
            Citation.id,
            Citation.citing_opinion_id,
            Citation.cited_opinion_id,
            Citation.depth,
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.citation_count
        ).join(
            OpinionCluster,
            Citation.cited_opinion_id == OpinionCluster.id
        ).filter(
            Citation.citing_opinion_id == opinion_id
        ).order_by(
            OpinionCluster.citation_count.desc()
        ).limit(10).all()

        return {
            "opinion_id": opinion_id,
            "case_name": opinion.case_name,
            "times_cited": times_cited,
            "times_citing": times_citing,
            "top_citing_cases": [
                {
                    "id": r.id,
                    "citing_opinion_id": r.citing_opinion_id,
                    "cited_opinion_id": r.cited_opinion_id,
                    "depth": r.depth,
                    "citing_case_name": r.case_name,
                    "citing_date_filed": str(r.date_filed) if r.date_filed else None,
                }
                for r in top_citing
            ],
            "top_cited_cases": [
                {
                    "id": r.id,
                    "citing_opinion_id": r.citing_opinion_id,
                    "cited_opinion_id": r.cited_opinion_id,
                    "depth": r.depth,
                    "cited_case_name": r.case_name,
                    "cited_date_filed": str(r.date_filed) if r.date_filed else None,
                }
                for r in top_cited
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting citation stats for {opinion_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving citation stats: {str(e)}")


@router.get("/{opinion_id}/network")
async def get_citation_network(
    opinion_id: int,
    db: Session = Depends(get_db),
    max_depth: int = Query(2, ge=1, le=3, description="Maximum depth to traverse"),
    max_nodes: int = Query(100, ge=10, le=500, description="Maximum nodes to return"),
):
    """
    Get citation network graph data for visualization.

    Returns nodes (opinions) and edges (citations) for network visualization.
    Explores citations up to max_depth levels away from the center opinion.

    Args:
        opinion_id: The center opinion for the network
        max_depth: How many levels of citations to explore (1-3)
        max_nodes: Maximum number of nodes to return
    """
    try:
        # Verify opinion exists
        center_opinion = db.query(OpinionCluster).filter(
            OpinionCluster.id == opinion_id
        ).first()

        if not center_opinion:
            raise HTTPException(status_code=404, detail=f"Opinion {opinion_id} not found")

        # Track visited opinion IDs and nodes
        visited: Set[int] = {opinion_id}
        nodes: Dict[int, CitationNetworkNode] = {}
        edges: List[CitationNetworkEdge] = []

        # Add center node
        nodes[opinion_id] = CitationNetworkNode(
            id=opinion_id,
            opinion_id=opinion_id,
            case_name=center_opinion.case_name or "Unknown",
            date_filed=str(center_opinion.date_filed) if center_opinion.date_filed else None,
            citation_count=center_opinion.citation_count or 0,
            precedential_status=center_opinion.precedential_status,
        )

        # BFS to explore citation network
        current_level = [opinion_id]

        for depth in range(max_depth):
            if len(nodes) >= max_nodes:
                break

            next_level = []

            for current_id in current_level:
                if len(nodes) >= max_nodes:
                    break

                # Get opinions citing this one (incoming edges)
                citing = db.query(
                    Citation.citing_opinion_id,
                    Citation.depth,
                    OpinionCluster.case_name,
                    OpinionCluster.date_filed,
                    OpinionCluster.citation_count,
                    OpinionCluster.precedential_status
                ).join(
                    OpinionCluster,
                    Citation.citing_opinion_id == OpinionCluster.id
                ).filter(
                    Citation.cited_opinion_id == current_id
                ).order_by(
                    OpinionCluster.citation_count.desc()
                ).limit(20).all()

                for c in citing:
                    if len(nodes) >= max_nodes:
                        break

                    if c.citing_opinion_id not in visited:
                        visited.add(c.citing_opinion_id)
                        nodes[c.citing_opinion_id] = CitationNetworkNode(
                            id=c.citing_opinion_id,
                            opinion_id=c.citing_opinion_id,
                            case_name=c.case_name or "Unknown",
                            date_filed=str(c.date_filed) if c.date_filed else None,
                            citation_count=c.citation_count or 0,
                            precedential_status=c.precedential_status,
                        )
                        next_level.append(c.citing_opinion_id)

                    # Add edge
                    edges.append(CitationNetworkEdge(
                        source=c.citing_opinion_id,
                        target=current_id,
                        depth=c.depth or 1
                    ))

                # Get opinions cited by this one (outgoing edges)
                cited = db.query(
                    Citation.cited_opinion_id,
                    Citation.depth,
                    OpinionCluster.case_name,
                    OpinionCluster.date_filed,
                    OpinionCluster.citation_count,
                    OpinionCluster.precedential_status
                ).join(
                    OpinionCluster,
                    Citation.cited_opinion_id == OpinionCluster.id
                ).filter(
                    Citation.citing_opinion_id == current_id
                ).order_by(
                    OpinionCluster.citation_count.desc()
                ).limit(20).all()

                for c in cited:
                    if len(nodes) >= max_nodes:
                        break

                    if c.cited_opinion_id not in visited:
                        visited.add(c.cited_opinion_id)
                        nodes[c.cited_opinion_id] = CitationNetworkNode(
                            id=c.cited_opinion_id,
                            opinion_id=c.cited_opinion_id,
                            case_name=c.case_name or "Unknown",
                            date_filed=str(c.date_filed) if c.date_filed else None,
                            citation_count=c.citation_count or 0,
                            precedential_status=c.precedential_status,
                        )
                        next_level.append(c.cited_opinion_id)

                    # Add edge
                    edges.append(CitationNetworkEdge(
                        source=current_id,
                        target=c.cited_opinion_id,
                        depth=c.depth or 1
                    ))

            current_level = next_level

        return CitationNetworkResponse(
            nodes=list(nodes.values()),
            edges=edges,
            center_opinion_id=opinion_id,
            max_depth=max_depth
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting citation network for {opinion_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving citation network: {str(e)}")


@router.get("/stats/most-cited")
async def get_most_cited_cases(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500, description="Number of cases to return"),
):
    """
    Get the most cited cases across the entire database.

    Returns cases ordered by how many times they are cited.
    """
    try:
        # Count citations for each opinion
        results = db.query(
            Citation.cited_opinion_id,
            func.count(Citation.id).label('citation_count'),
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.precedential_status
        ).join(
            OpinionCluster,
            Citation.cited_opinion_id == OpinionCluster.id
        ).group_by(
            Citation.cited_opinion_id,
            OpinionCluster.case_name,
            OpinionCluster.date_filed,
            OpinionCluster.precedential_status
        ).order_by(
            func.count(Citation.id).desc()
        ).limit(limit).all()

        return {
            "most_cited": [
                {
                    "opinion_id": r.cited_opinion_id,
                    "case_name": r.case_name,
                    "date_filed": str(r.date_filed) if r.date_filed else None,
                    "times_cited": r.citation_count,
                    "precedential_status": r.precedential_status,
                }
                for r in results
            ],
            "total": len(results)
        }

    except Exception as e:
        logger.error(f"Error getting most cited cases: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving most cited cases: {str(e)}")
