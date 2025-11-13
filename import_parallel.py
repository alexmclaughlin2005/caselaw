#!/usr/bin/env python3
"""
Parallel import script for Railway - imports independent tables concurrently.
Run this via: python import_parallel.py
"""
import sys
import logging
from pathlib import Path
import threading
from typing import List, Tuple

# Add app to path
sys.path.insert(0, '/app')

from app.services.data_importer import DataImporter
from app.core.database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(threadName)s - %(message)s')
logger = logging.getLogger(__name__)

def import_table(table_name: str, s3_file: str, date: str) -> int:
    """Import a single table in its own thread with its own DB session."""
    import time

    importer = DataImporter()
    session = SessionLocal()
    table_start = time.time()

    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"[{table_name}] Starting import in thread {threading.current_thread().name}...")
        logger.info(f"{'='*60}")

        # Check if already downloaded
        csv_path = Path(f"/app/data/{table_name}-{date}.csv")

        if not csv_path.exists():
            logger.error(f"[{table_name}] File not found: {csv_path}")
            return 0

        logger.info(f"[{table_name}] File size: {csv_path.stat().st_size / (1024**3):.2f} GB")
        logger.info(f"[{table_name}] Starting database import...")

        row_count = importer.import_csv(table_name, csv_path, session)

        table_elapsed = time.time() - table_start
        logger.info(f"\n[{table_name}] ✅ TABLE COMPLETE | {row_count:,} rows | Total time: {table_elapsed/60:.1f} minutes")

        return row_count

    except Exception as e:
        table_elapsed = time.time() - table_start
        logger.error(f"[{table_name}] ❌ ERROR after {table_elapsed/60:.1f} minutes: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        session.close()


def main():
    """Import caselaw tables with parallel processing where possible."""
    import time

    date = "2025-10-31"
    overall_start = time.time()

    # Phase 1: Import dockets and citations in parallel (no dependencies)
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: PARALLEL IMPORT - Dockets & Citations")
    logger.info("=" * 80)

    parallel_tables = [
        ("search_docket", f"dockets-{date}.csv.bz2"),
        ("search_opinionscited", f"opinions-cited-{date}.csv.bz2"),
    ]

    # Create threads for parallel import
    threads: List[threading.Thread] = []
    results = {}

    for table_name, s3_file in parallel_tables:
        thread = threading.Thread(
            target=lambda tn=table_name, sf=s3_file: results.update({tn: import_table(tn, sf, date)}),
            name=f"Import-{table_name}"
        )
        threads.append(thread)
        thread.start()
        logger.info(f"Started thread for {table_name}")

    # Wait for all parallel imports to complete
    for thread in threads:
        thread.join()

    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 COMPLETE - Parallel imports finished")
    logger.info("=" * 80)

    # Phase 2: Import opinion clusters (depends on dockets)
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: SEQUENTIAL IMPORT - Opinion Clusters (depends on dockets)")
    logger.info("=" * 80)

    results["search_opinioncluster"] = import_table(
        "search_opinioncluster",
        f"opinion-clusters-{date}.csv.bz2",
        date
    )

    # Phase 3: Import parentheticals (independent, could have been parallel but keeping it simple)
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: IMPORT - Parentheticals")
    logger.info("=" * 80)

    results["search_parenthetical"] = import_table(
        "search_parenthetical",
        f"parentheticals-{date}.csv.bz2",
        date
    )

    overall_elapsed = time.time() - overall_start
    logger.info("\n" + "=" * 80)
    logger.info("🎉 ALL PARALLEL IMPORTS COMPLETE!")
    logger.info(f"Total time: {overall_elapsed/3600:.1f} hours ({overall_elapsed/60:.1f} minutes)")
    logger.info("\nImport Summary:")
    for table_name, row_count in results.items():
        logger.info(f"  {table_name}: {row_count:,} rows")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
