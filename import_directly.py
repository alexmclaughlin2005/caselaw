#!/usr/bin/env python3
"""
Direct import script for Railway - no threading, just sequential imports.
Run this via Railway shell: python import_directly.py
"""
import sys
import logging
from pathlib import Path

# Add app to path
sys.path.insert(0, '/app')

from app.services.s3_downloader import CourtListenerDownloader
from app.services.data_importer import DataImporter
from app.core.database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Import people database tables first, then caselaw tables."""

    downloader = CourtListenerDownloader()
    importer = DataImporter()
    date = "2025-10-31"

    # Step 1: Import people database (required for foreign keys)
    logger.info("=" * 80)
    logger.info("STEP 1: IMPORTING PEOPLE DATABASE")
    logger.info("=" * 80)

    people_tables = [
        ("people_db_court", f"courts-{date}.csv.bz2"),
        ("people_db_person", f"people-db-people-{date}.csv.bz2"),
    ]

    session = SessionLocal()

    for table_name, s3_file in people_tables:
        try:
            logger.info(f"\n[{table_name}] Starting...")

            # Check if already downloaded
            csv_path = Path(f"/app/data/{table_name}-{date}.csv")

            if not csv_path.exists():
                logger.info(f"[{table_name}] Downloading from S3: {s3_file}")
                csv_path = downloader.download_file(
                    key=f"bulk-data/{s3_file}",
                    target_path=csv_path
                )
                logger.info(f"[{table_name}] Downloaded: {csv_path.stat().st_size / (1024**2):.2f} MB")
            else:
                logger.info(f"[{table_name}] File already exists, skipping download")

            # Import
            logger.info(f"[{table_name}] Importing to database...")

            if table_name == "people_db_person":
                # Use pandas with self-referential FK skip
                row_count = importer.import_csv_pandas(
                    table_name, csv_path, session, skip_self_referential_fk=True
                )
            else:
                row_count = importer.import_csv(table_name, csv_path, session)

            logger.info(f"[{table_name}] ✓ Complete: {row_count:,} rows")

        except Exception as e:
            logger.error(f"[{table_name}] ERROR: {e}")
            import traceback
            traceback.print_exc()
            continue

    session.close()

    # Step 2: Import caselaw tables (using already downloaded files if available)
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: IMPORTING CASELAW TABLES")
    logger.info("=" * 80)

    caselaw_tables = [
        ("search_docket", f"dockets-{date}.csv.bz2"),
        ("search_opinioncluster", f"opinion-clusters-{date}.csv.bz2"),
        ("search_opinionscited", f"opinions-cited-{date}.csv.bz2"),
        ("search_parenthetical", f"parentheticals-{date}.csv.bz2"),
    ]

    session = SessionLocal()

    import time
    overall_start = time.time()

    for table_name, s3_file in caselaw_tables:
        table_start = time.time()
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"[{table_name}] Starting import...")
            logger.info(f"{'='*60}")

            # Check if already downloaded
            csv_path = Path(f"/app/data/{table_name}-{date}.csv")

            if not csv_path.exists():
                logger.info(f"[{table_name}] Downloading from S3: {s3_file}")
                csv_path = downloader.download_file(
                    key=f"bulk-data/{s3_file}",
                    target_path=csv_path
                )
                logger.info(f"[{table_name}] Downloaded: {csv_path.stat().st_size / (1024**3):.2f} GB")
            else:
                logger.info(f"[{table_name}] File already exists at {csv_path}")
                logger.info(f"[{table_name}] File size: {csv_path.stat().st_size / (1024**3):.2f} GB")

            # Import with detailed progress (data_importer.py now handles progress logging)
            logger.info(f"[{table_name}] Starting database import...")
            row_count = importer.import_csv(table_name, csv_path, session)

            table_elapsed = time.time() - table_start
            logger.info(f"\n[{table_name}] ✅ TABLE COMPLETE | {row_count:,} rows | Total time: {table_elapsed/60:.1f} minutes")

        except Exception as e:
            table_elapsed = time.time() - table_start
            logger.error(f"[{table_name}] ❌ ERROR after {table_elapsed/60:.1f} minutes: {e}")
            import traceback
            traceback.print_exc()
            continue

    session.close()

    overall_elapsed = time.time() - overall_start
    logger.info("\n" + "=" * 80)
    logger.info("🎉 ALL CASELAW IMPORTS COMPLETE!")
    logger.info(f"Total time: {overall_elapsed/3600:.1f} hours ({overall_elapsed/60:.1f} minutes)")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
