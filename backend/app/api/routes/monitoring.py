"""
Monitoring API Routes

Endpoints for monitoring database import progress and system status
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db

router = APIRouter()


@router.get("/database/counts")
async def get_database_counts(db: Session = Depends(get_db)):
    """
    Get current record counts for all tables.
    Useful for monitoring import progress.
    """
    try:
        # Query counts for all main tables
        counts = {}

        tables = [
            "search_docket",
            "search_opinioncluster",
            "search_opinionscited",
            "search_parenthetical"
        ]

        for table in tables:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            counts[table] = count

        # Get database size
        result = db.execute(text("""
            SELECT pg_size_pretty(pg_database_size(current_database())) as size
        """))
        db_size = result.scalar()

        # Get table sizes
        table_sizes = {}
        for table in tables:
            result = db.execute(text(f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table}')) as size
            """))
            table_sizes[table] = result.scalar()

        return {
            "counts": counts,
            "database_size": db_size,
            "table_sizes": table_sizes,
            "total_records": sum(counts.values())
        }

    except Exception as e:
        return {
            "error": str(e),
            "counts": {},
            "database_size": "0 bytes",
            "table_sizes": {},
            "total_records": 0
        }


@router.get("/database/activity")
async def get_database_activity(db: Session = Depends(get_db)):
    """
    Get current database activity - active connections and queries.
    """
    try:
        # Get active connections
        result = db.execute(text("""
            SELECT
                count(*) as connection_count,
                count(*) FILTER (WHERE state = 'active') as active_queries,
                count(*) FILTER (WHERE state = 'idle') as idle_connections
            FROM pg_stat_activity
            WHERE datname = current_database()
        """))

        row = result.fetchone()

        # Get long-running queries
        result = db.execute(text("""
            SELECT
                pid,
                query,
                state,
                EXTRACT(EPOCH FROM (now() - query_start)) as duration_seconds
            FROM pg_stat_activity
            WHERE
                datname = current_database()
                AND state = 'active'
                AND query NOT LIKE '%pg_stat_activity%'
            ORDER BY query_start
            LIMIT 10
        """))

        active_queries = []
        for row_query in result:
            active_queries.append({
                "pid": row_query[0],
                "query": row_query[1][:100] + "..." if len(row_query[1]) > 100 else row_query[1],
                "state": row_query[2],
                "duration_seconds": float(row_query[3]) if row_query[3] else 0
            })

        return {
            "connection_count": row[0],
            "active_queries": row[1],
            "idle_connections": row[2],
            "active_query_details": active_queries
        }

    except Exception as e:
        return {
            "error": str(e),
            "connection_count": 0,
            "active_queries": 0,
            "idle_connections": 0,
            "active_query_details": []
        }


@router.get("/import/progress")
async def get_import_progress(db: Session = Depends(get_db)):
    """
    Get import progress by comparing current counts to expected totals.
    """
    # Expected final counts (from your local database)
    expected_counts = {
        "search_docket": 70000000,  # ~70M
        "search_opinioncluster": 6000000,  # ~6M
        "search_opinionscited": 76000000,  # ~76M
        "search_parenthetical": 6000000  # ~6M
    }

    try:
        # Get current counts
        current_counts = {}
        progress = {}

        for table, expected in expected_counts.items():
            result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            current = result.scalar()
            current_counts[table] = current

            # Calculate progress percentage
            pct = (current / expected * 100) if expected > 0 else 0
            progress[table] = {
                "current": current,
                "expected": expected,
                "percentage": round(pct, 2),
                "remaining": expected - current,
                "status": "completed" if current >= expected else "importing" if current > 0 else "pending"
            }

        # Calculate overall progress
        total_current = sum(current_counts.values())
        total_expected = sum(expected_counts.values())
        overall_percentage = (total_current / total_expected * 100) if total_expected > 0 else 0

        return {
            "tables": progress,
            "overall": {
                "current": total_current,
                "expected": total_expected,
                "percentage": round(overall_percentage, 2),
                "remaining": total_expected - total_current
            }
        }

    except Exception as e:
        return {
            "error": str(e),
            "tables": {},
            "overall": {
                "current": 0,
                "expected": 0,
                "percentage": 0,
                "remaining": 0
            }
        }
