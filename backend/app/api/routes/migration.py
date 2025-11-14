"""
Database Migration Routes

Provides endpoints to run database migrations.
Useful for Railway deployment where direct database access is limited.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.api.deps import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/run-chunk-table-migration")
async def run_chunk_table_migration(db: Session = Depends(get_db)):
    """
    Create the csv_chunk_progress table and indexes.

    This endpoint creates the table needed for the CSV chunking system.
    Safe to run multiple times - uses CREATE TABLE IF NOT EXISTS.

    Returns:
        Dictionary with migration status and table information
    """
    try:
        logger.info("Running CSV chunk progress table migration...")

        # Check if table exists
        check_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'csv_chunk_progress'
            );
        """)

        exists = db.execute(check_sql).scalar()

        if exists:
            logger.info("Table already exists, skipping creation")
            return {
                "status": "already_exists",
                "message": "Table 'csv_chunk_progress' already exists",
                "table_exists": True
            }

        # Create table
        logger.info("Creating csv_chunk_progress table...")

        create_table_sql = text("""
            CREATE TABLE csv_chunk_progress (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                dataset_date VARCHAR(20) NOT NULL,
                chunk_number INTEGER NOT NULL,
                chunk_filename VARCHAR(255) NOT NULL,
                chunk_start_row BIGINT,
                chunk_end_row BIGINT,
                chunk_row_count BIGINT,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                rows_imported BIGINT DEFAULT 0,
                rows_skipped BIGINT DEFAULT 0,
                started_at TIMESTAMPTZ,
                completed_at TIMESTAMPTZ,
                duration_seconds INTEGER,
                error_message TEXT,
                retry_count INTEGER NOT NULL DEFAULT 0,
                import_method VARCHAR(50),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)

        db.execute(create_table_sql)
        db.commit()

        logger.info("Table created successfully")

        # Create indexes
        logger.info("Creating indexes...")

        indexes = [
            "CREATE INDEX ix_csv_chunk_progress_table_name ON csv_chunk_progress(table_name);",
            "CREATE INDEX ix_csv_chunk_progress_dataset_date ON csv_chunk_progress(dataset_date);",
            "CREATE INDEX ix_csv_chunk_progress_chunk_number ON csv_chunk_progress(chunk_number);",
            "CREATE INDEX ix_csv_chunk_progress_status ON csv_chunk_progress(status);",
            "CREATE INDEX ix_csv_chunk_progress_table_date ON csv_chunk_progress(table_name, dataset_date);"
        ]

        for idx_sql in indexes:
            db.execute(text(idx_sql))

        db.commit()

        logger.info("All indexes created successfully")

        # Get column count for verification
        count_sql = text("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'csv_chunk_progress';
        """)

        column_count = db.execute(count_sql).scalar()

        logger.info(f"Migration complete! Table has {column_count} columns")

        return {
            "status": "success",
            "message": "Table 'csv_chunk_progress' created successfully",
            "table_exists": True,
            "column_count": column_count,
            "indexes_created": len(indexes)
        }

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Migration failed: {str(e)}"
        )


@router.get("/check-chunk-table")
async def check_chunk_table(db: Session = Depends(get_db)):
    """
    Check if the csv_chunk_progress table exists.

    Returns:
        Dictionary with table status and column information
    """
    try:
        # Check if table exists
        check_sql = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'csv_chunk_progress'
            );
        """)

        exists = db.execute(check_sql).scalar()

        if not exists:
            return {
                "table_exists": False,
                "message": "Table 'csv_chunk_progress' does not exist. Run POST /api/migration/run-chunk-table-migration to create it."
            }

        # Get column info
        columns_sql = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'csv_chunk_progress'
            ORDER BY ordinal_position;
        """)

        columns = db.execute(columns_sql).fetchall()

        return {
            "table_exists": True,
            "message": "Table 'csv_chunk_progress' exists and is ready to use",
            "column_count": len(columns),
            "columns": [
                {
                    "name": col[0],
                    "type": col[1],
                    "nullable": col[2]
                }
                for col in columns
            ]
        }

    except Exception as e:
        logger.error(f"Check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Check failed: {str(e)}"
        )
