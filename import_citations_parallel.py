#!/usr/bin/env python3
"""
Start citations import in parallel with the already-running dockets import.
This script imports ONLY search_opinionscited which has no foreign key dependencies.
"""
import sys
import logging
from pathlib import Path
import time

# Add app to path
sys.path.insert(0, '/app')

from app.services.data_importer import DataImporter
from app.core.database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Import citations table in parallel with dockets."""

    date = "2025-10-31"
    table_name = "search_opinionscited"

    importer = DataImporter()
    session = SessionLocal()

    try:
        logger.info("=" * 80)
        logger.info("PARALLEL IMPORT: Citations (search_opinionscited)")
        logger.info("This will run alongside the dockets import for faster completion")
        logger.info("=" * 80)

        csv_path = Path(f"/app/data/{table_name}-{date}.csv")

        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return

        logger.info(f"[{table_name}] File size: {csv_path.stat().st_size / (1024**3):.2f} GB")
        logger.info(f"[{table_name}] Starting database import...")

        start_time = time.time()
        row_count = importer.import_csv(table_name, csv_path, session)
        elapsed = time.time() - start_time

        logger.info(f"\n[{table_name}] ✅ COMPLETE | {row_count:,} rows | Time: {elapsed/60:.1f} minutes")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    main()
