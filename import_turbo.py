#!/usr/bin/env python3
"""
TURBO MODE: High-performance multi-threaded import with FK checks disabled.
Uses multiple parallel workers per table for maximum throughput.
"""
import sys
import logging
from pathlib import Path
import threading
import queue
from typing import List, Tuple
import time

# Add app to path
sys.path.insert(0, '/app')

from app.services.data_importer import DataImporter
from app.core.database import SessionLocal
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(threadName)s] - %(message)s'
)
logger = logging.getLogger(__name__)


def disable_foreign_keys(session):
    """Disable foreign key checks for faster imports."""
    logger.info("🚀 TURBO MODE: Disabling foreign key checks for maximum performance")
    session.execute(text("SET session_replication_role = 'replica';"))
    session.commit()
    logger.info("✓ Foreign key checks disabled")


def enable_foreign_keys(session):
    """Re-enable foreign key checks after import."""
    logger.info("Re-enabling foreign key checks...")
    session.execute(text("SET session_replication_role = 'origin';"))
    session.commit()
    logger.info("✓ Foreign key checks re-enabled")


def import_table_worker(
    table_name: str,
    csv_path: Path,
    worker_id: int,
    start_row: int,
    end_row: int,
    results_queue: queue.Queue
):
    """
    Worker thread that imports a specific range of rows from a CSV file.

    Args:
        table_name: Name of the table to import to
        csv_path: Path to CSV file
        worker_id: ID of this worker thread
        start_row: Starting row number (0-indexed)
        end_row: Ending row number (exclusive)
        results_queue: Queue to put results
    """
    thread_start = time.time()

    try:
        # Each worker gets its own database session
        session = SessionLocal()

        # Disable FK checks for this session
        session.execute(text("SET session_replication_role = 'replica';"))
        session.commit()

        importer = DataImporter()

        logger.info(f"Worker-{worker_id} starting: rows {start_row:,} to {end_row:,}")

        # Import the specified range
        # We'll need to modify the importer to support row ranges
        row_count = importer.import_csv_range(
            table_name=table_name,
            csv_path=csv_path,
            session=session,
            start_row=start_row,
            end_row=end_row,
            worker_id=worker_id
        )

        elapsed = time.time() - thread_start
        rate = (row_count / elapsed * 60) if elapsed > 0 else 0

        logger.info(f"Worker-{worker_id} ✅ COMPLETE | {row_count:,} rows | "
                   f"Time: {elapsed/60:.1f}m | Rate: {rate:,.0f} rows/min")

        # Re-enable FK checks for this session
        session.execute(text("SET session_replication_role = 'origin';"))
        session.commit()
        session.close()

        results_queue.put({
            'worker_id': worker_id,
            'row_count': row_count,
            'elapsed': elapsed,
            'success': True
        })

    except Exception as e:
        logger.error(f"Worker-{worker_id} ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        results_queue.put({
            'worker_id': worker_id,
            'row_count': 0,
            'elapsed': time.time() - thread_start,
            'success': False,
            'error': str(e)
        })


def count_csv_rows(csv_path: Path) -> int:
    """Quickly count rows in CSV file."""
    logger.info(f"Counting rows in {csv_path.name}...")
    import subprocess
    result = subprocess.run(
        ['wc', '-l', str(csv_path)],
        capture_output=True,
        text=True
    )
    row_count = int(result.stdout.split()[0])
    logger.info(f"CSV contains {row_count:,} rows")
    return row_count


def import_table_parallel(
    table_name: str,
    csv_path: Path,
    num_workers: int = 4
) -> dict:
    """
    Import a table using multiple parallel workers.

    Args:
        table_name: Name of the table
        csv_path: Path to CSV file
        num_workers: Number of parallel worker threads

    Returns:
        dict with import statistics
    """
    overall_start = time.time()

    logger.info("=" * 80)
    logger.info(f"TURBO MODE PARALLEL IMPORT: {table_name}")
    logger.info(f"Workers: {num_workers} parallel threads")
    logger.info(f"File: {csv_path.name} ({csv_path.stat().st_size / (1024**3):.2f} GB)")
    logger.info("=" * 80)

    # Count total rows
    total_rows = count_csv_rows(csv_path)

    # Calculate row ranges for each worker
    rows_per_worker = total_rows // num_workers

    # Create worker threads
    threads: List[threading.Thread] = []
    results_queue = queue.Queue()

    for i in range(num_workers):
        start_row = i * rows_per_worker
        end_row = (i + 1) * rows_per_worker if i < num_workers - 1 else total_rows

        thread = threading.Thread(
            target=import_table_worker,
            args=(table_name, csv_path, i, start_row, end_row, results_queue),
            name=f"Worker-{i}"
        )
        threads.append(thread)
        thread.start()
        logger.info(f"Started Worker-{i}: rows {start_row:,} to {end_row:,}")

    # Wait for all workers to complete
    for thread in threads:
        thread.join()

    # Collect results
    total_imported = 0
    successful_workers = 0

    while not results_queue.empty():
        result = results_queue.get()
        if result['success']:
            total_imported += result['row_count']
            successful_workers += 1

    overall_elapsed = time.time() - overall_start
    overall_rate = (total_imported / overall_elapsed * 60) if overall_elapsed > 0 else 0

    logger.info("=" * 80)
    logger.info(f"🎉 PARALLEL IMPORT COMPLETE: {table_name}")
    logger.info(f"Total rows imported: {total_imported:,}")
    logger.info(f"Successful workers: {successful_workers}/{num_workers}")
    logger.info(f"Total time: {overall_elapsed/60:.1f} minutes")
    logger.info(f"Overall rate: {overall_rate:,.0f} rows/min")
    logger.info("=" * 80)

    return {
        'table_name': table_name,
        'total_rows': total_imported,
        'elapsed': overall_elapsed,
        'rate': overall_rate,
        'workers': num_workers
    }


def main():
    """
    TURBO MODE: Import with maximum parallelization and FK checks disabled.
    """
    date = "2025-10-31"

    # Tables to import in parallel
    tables = [
        ("search_docket", f"dockets-{date}.csv.bz2", 4),  # 4 workers
        ("search_opinionscited", f"opinions-cited-{date}.csv.bz2", 4),  # 4 workers
    ]

    overall_start = time.time()
    results = []

    logger.info("\n" + "=" * 80)
    logger.info("🚀 TURBO MODE IMPORT STARTING")
    logger.info("Features:")
    logger.info("  ✓ Foreign key checks DISABLED for maximum speed")
    logger.info("  ✓ Multiple parallel workers per table")
    logger.info("  ✓ Large 500K row chunks")
    logger.info("  ✓ 5M row commit intervals")
    logger.info("=" * 80)

    # Create a master session for FK management
    master_session = SessionLocal()

    try:
        # Disable FK checks globally
        disable_foreign_keys(master_session)

        # Import each table with parallel workers
        for table_name, s3_file, num_workers in tables:
            csv_path = Path(f"/app/data/{table_name}-{date}.csv")

            if not csv_path.exists():
                logger.warning(f"CSV not found: {csv_path}")
                continue

            result = import_table_parallel(table_name, csv_path, num_workers)
            results.append(result)

        # Re-enable FK checks
        enable_foreign_keys(master_session)

    except Exception as e:
        logger.error(f"TURBO MODE ERROR: {e}")
        import traceback
        traceback.print_exc()
        # Make sure to re-enable FK checks even on error
        try:
            enable_foreign_keys(master_session)
        except:
            pass
    finally:
        master_session.close()

    overall_elapsed = time.time() - overall_start

    logger.info("\n" + "=" * 80)
    logger.info("🎉 TURBO MODE IMPORT COMPLETE!")
    logger.info(f"Total time: {overall_elapsed/3600:.1f} hours ({overall_elapsed/60:.1f} minutes)")
    logger.info("\nResults:")
    for result in results:
        logger.info(f"  {result['table_name']}: {result['total_rows']:,} rows @ {result['rate']:,.0f} rows/min")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
