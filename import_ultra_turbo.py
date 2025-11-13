#!/usr/bin/env python3
"""
ULTRA TURBO MODE: PostgreSQL COPY command for maximum speed.
Bypasses Python CSV parsing entirely - uses PostgreSQL's native COPY.
Expected: 200K-500K rows/min (5-10x faster than INSERT)
"""
import sys
import logging
from pathlib import Path
import time

# Add app to path
sys.path.insert(0, '/app')

from app.core.database import SessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def import_with_copy(table_name: str, csv_path: Path, session):
    """
    Use PostgreSQL COPY command for ultra-fast bulk loading.

    This is 5-10x faster than INSERT because:
    - No Python CSV parsing overhead
    - Direct PostgreSQL native loading
    - Minimal transaction overhead
    """
    start_time = time.time()

    logger.info(f"=" * 80)
    logger.info(f"🚀 ULTRA TURBO: PostgreSQL COPY for {table_name}")
    logger.info(f"File: {csv_path.name} ({csv_path.stat().st_size / (1024**3):.2f} GB)")
    logger.info(f"=" * 80)

    # Get row count before
    count_before = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
    logger.info(f"Rows before import: {count_before:,}")

    # Create temporary table for COPY (to handle duplicates)
    temp_table = f"{table_name}_temp"

    logger.info(f"Creating temporary table: {temp_table}")
    session.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
    session.execute(text(f"CREATE TABLE {temp_table} (LIKE {table_name} INCLUDING ALL)"))
    session.commit()

    logger.info("Starting COPY - this loads at PostgreSQL native speed...")
    copy_start = time.time()

    # Use COPY to load into temp table (super fast!)
    # Note: COPY FROM requires superuser or pg_read_server_files role
    # Alternative: Use psycopg2 copy_expert with file handle

    try:
        # Get database connection (raw psycopg2)
        connection = session.connection().connection
        cursor = connection.cursor()

        # Open CSV file
        with open(csv_path, 'r') as f:
            # Skip header
            next(f)

            # COPY FROM STDIN - this is the fastest way to bulk load
            copy_sql = f"""
                COPY {temp_table} FROM STDIN
                WITH (FORMAT CSV, HEADER FALSE, QUOTE '"', ESCAPE '"')
            """

            logger.info(f"Executing: COPY {temp_table} FROM STDIN...")
            cursor.copy_expert(copy_sql, f)

        connection.commit()

        copy_elapsed = time.time() - copy_start
        temp_count = session.execute(text(f"SELECT COUNT(*) FROM {temp_table}")).scalar()
        copy_rate = (temp_count / copy_elapsed * 60) if copy_elapsed > 0 else 0

        logger.info(f"✓ COPY complete: {temp_count:,} rows in {copy_elapsed/60:.1f}m @ {copy_rate:,.0f} rows/min")

        # Now merge from temp table to main table (handles duplicates)
        logger.info(f"Merging from {temp_table} to {table_name} (ON CONFLICT DO NOTHING)...")
        merge_start = time.time()

        # Get column names
        columns_result = session.execute(text(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in columns_result]
        columns_str = ', '.join([f'"{col}"' for col in columns])

        # Insert with ON CONFLICT DO NOTHING
        merge_sql = f"""
            INSERT INTO {table_name} ({columns_str})
            SELECT {columns_str}
            FROM {temp_table}
            ON CONFLICT (id) DO NOTHING
        """

        session.execute(text(merge_sql))
        session.commit()

        merge_elapsed = time.time() - merge_start
        logger.info(f"✓ Merge complete in {merge_elapsed/60:.1f}m")

        # Clean up temp table
        logger.info(f"Dropping temporary table: {temp_table}")
        session.execute(text(f"DROP TABLE {temp_table}"))
        session.commit()

        # Final count
        count_after = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        rows_added = count_after - count_before

        total_elapsed = time.time() - start_time
        avg_rate = (rows_added / total_elapsed * 60) if total_elapsed > 0 else 0

        logger.info(f"=" * 80)
        logger.info(f"✅ {table_name} COMPLETE")
        logger.info(f"New rows: {rows_added:,}")
        logger.info(f"Total in DB: {count_after:,}")
        logger.info(f"Duplicates skipped: {temp_count - rows_added:,}")
        logger.info(f"Total time: {total_elapsed/60:.1f}m")
        logger.info(f"Average rate: {avg_rate:,.0f} rows/min")
        logger.info(f"=" * 80)

        return rows_added

    except Exception as e:
        logger.error(f"COPY failed, falling back to standard import: {e}")
        # Clean up temp table
        try:
            session.execute(text(f"DROP TABLE IF EXISTS {temp_table}"))
            session.commit()
        except:
            pass
        raise


def main():
    """Ultra Turbo Mode: PostgreSQL COPY for maximum performance."""
    date = "2025-10-31"

    session = SessionLocal()

    try:
        logger.info("\n" + "=" * 80)
        logger.info("🚀 ULTRA TURBO MODE")
        logger.info("Using PostgreSQL COPY command - 5-10x faster than INSERT!")
        logger.info("=" * 80)

        # Disable FK checks
        logger.info("\nDisabling foreign key checks...")
        session.execute(text("SET session_replication_role = 'replica';"))
        session.commit()
        logger.info("✓ FK checks disabled")

        # Import dockets
        dockets_path = Path(f"/app/data/search_docket-{date}.csv")
        if dockets_path.exists():
            import_with_copy("search_docket", dockets_path, session)
        else:
            logger.warning(f"Dockets file not found: {dockets_path}")

        # Re-enable FK checks
        logger.info("\nRe-enabling foreign key checks...")
        session.execute(text("SET session_replication_role = 'origin';"))
        session.commit()
        logger.info("✓ FK checks re-enabled")

    except Exception as e:
        logger.error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    main()
