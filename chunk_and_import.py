#!/usr/bin/env python3
"""
Standalone CLI script for chunking large CSV files and importing them sequentially.

This script provides a command-line interface for:
1. Chunking large CSV files into manageable pieces
2. Importing chunks sequentially with progress tracking
3. Monitoring import progress
4. Resuming failed imports

Usage:
    # Chunk a CSV file
    python chunk_and_import.py chunk --table search_docket --date 2025-10-31 --chunk-size 1000000

    # Import chunks
    python chunk_and_import.py import --table search_docket --date 2025-10-31 --method standard

    # Check progress
    python chunk_and_import.py progress --table search_docket --date 2025-10-31

    # Reset chunks (for re-import)
    python chunk_and_import.py reset --table search_docket --date 2025-10-31

    # Delete chunks
    python chunk_and_import.py delete --table search_docket --date 2025-10-31 --delete-files
"""
import sys
import argparse
import logging
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.csv_chunk_manager import CSVChunkManager
from app.core.database import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def chunk_command(args):
    """Chunk a CSV file."""
    session = SessionLocal()
    chunk_manager = CSVChunkManager()

    try:
        # Construct CSV filename
        csv_filename = f"{args.table}-{args.date}.csv"
        csv_path = Path(chunk_manager.data_dir) / csv_filename

        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            sys.exit(1)

        logger.info(f"Chunking {csv_filename}...")
        logger.info(f"Table: {args.table}")
        logger.info(f"Date: {args.date}")
        logger.info(f"Chunk size: {args.chunk_size:,} rows")

        # Create chunks
        chunk_files = chunk_manager.chunk_csv(
            csv_path=csv_path,
            table_name=args.table,
            dataset_date=args.date,
            chunk_size=args.chunk_size,
            db_session=session
        )

        logger.info(f"\n✓ Successfully created {len(chunk_files)} chunks")

        # Show progress summary
        summary = chunk_manager.get_progress_summary(
            table_name=args.table,
            dataset_date=args.date,
            db_session=session
        )

        logger.info(f"\nChunk Summary:")
        logger.info(f"  Total chunks: {summary['total_chunks']}")
        logger.info(f"  Total rows: {summary['total_rows']:,}")
        logger.info(f"  Status: {summary['status']}")

    except Exception as e:
        logger.error(f"Error during chunking: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def import_command(args):
    """Import chunks sequentially."""
    session = SessionLocal()
    chunk_manager = CSVChunkManager()

    try:
        logger.info(f"Starting chunked import...")
        logger.info(f"Table: {args.table}")
        logger.info(f"Date: {args.date}")
        logger.info(f"Method: {args.method}")
        logger.info(f"Resume: {args.resume}")
        logger.info(f"Max retries: {args.max_retries}")

        # Check if chunks exist
        chunks = chunk_manager.get_chunks(
            table_name=args.table,
            dataset_date=args.date,
            db_session=session
        )

        if not chunks:
            logger.error(f"No chunks found for {args.table} on {args.date}")
            logger.error(f"Run the 'chunk' command first to create chunks")
            sys.exit(1)

        logger.info(f"Found {len(chunks)} chunks to process\n")

        # Start import
        results = chunk_manager.import_chunked(
            table_name=args.table,
            dataset_date=args.date,
            import_method=args.method,
            resume=args.resume,
            max_retries=args.max_retries,
            db_session=session
        )

        # Print results
        logger.info(f"\n{'='*80}")
        logger.info(f"IMPORT COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Table: {results['table_name']}")
        logger.info(f"Date: {results['dataset_date']}")
        logger.info(f"Total chunks: {results['total_chunks']}")
        logger.info(f"Successful: {results['successful_chunks']}")
        logger.info(f"Failed: {results['failed_chunks']}")
        logger.info(f"Skipped: {results['skipped_chunks']}")
        logger.info(f"Rows imported: {results['total_rows_imported']:,}")
        logger.info(f"Method: {results['import_method']}")

        if results['errors']:
            logger.info(f"\nErrors encountered:")
            for error in results['errors']:
                logger.error(f"  Chunk {error['chunk']}: {error['error'][:100]}")

        # Exit with error code if there were failures
        if results['failed_chunks'] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


def progress_command(args):
    """Show import progress."""
    session = SessionLocal()
    chunk_manager = CSVChunkManager()

    try:
        # Get progress summary
        summary = chunk_manager.get_progress_summary(
            table_name=args.table,
            dataset_date=args.date,
            db_session=session
        )

        if summary['total_chunks'] == 0:
            logger.info(f"No chunks found for {args.table} on {args.date}")
            sys.exit(0)

        logger.info(f"\n{'='*80}")
        logger.info(f"IMPORT PROGRESS")
        logger.info(f"{'='*80}")
        logger.info(f"Table: {summary['table_name']}")
        logger.info(f"Date: {summary['dataset_date']}")
        logger.info(f"Status: {summary['status']}")
        logger.info(f"\nChunks:")
        logger.info(f"  Total: {summary['total_chunks']}")
        logger.info(f"  Completed: {summary['completed_chunks']}")
        logger.info(f"  Failed: {summary['failed_chunks']}")
        logger.info(f"  Processing: {summary['processing_chunks']}")
        logger.info(f"  Pending: {summary['pending_chunks']}")
        logger.info(f"\nRows:")
        logger.info(f"  Total: {summary['total_rows']:,}")
        logger.info(f"  Imported: {summary['imported_rows']:,}")
        logger.info(f"  Skipped: {summary['skipped_rows']:,}")
        logger.info(f"\nProgress: {summary['progress_percentage']:.1f}%")

        # Show detailed chunk status if requested
        if args.detailed:
            chunks = chunk_manager.get_chunks(
                table_name=args.table,
                dataset_date=args.date,
                db_session=session
            )

            logger.info(f"\n{'='*80}")
            logger.info(f"DETAILED CHUNK STATUS")
            logger.info(f"{'='*80}")

            for chunk in chunks:
                status_icon = {
                    'completed': '✓',
                    'failed': '✗',
                    'processing': '⏳',
                    'pending': '○'
                }.get(chunk['status'], '?')

                logger.info(f"\nChunk {chunk['chunk_number']:4d}: {status_icon} {chunk['status']}")
                logger.info(f"  File: {chunk['chunk_filename']}")
                if chunk['chunk_row_count']:
                    logger.info(f"  Rows: {chunk['chunk_row_count']:,}")
                if chunk['rows_imported']:
                    logger.info(f"  Imported: {chunk['rows_imported']:,}")
                if chunk['duration_seconds']:
                    logger.info(f"  Duration: {chunk['duration_seconds']}s")
                if chunk['error_message']:
                    logger.info(f"  Error: {chunk['error_message'][:100]}")

    except Exception as e:
        logger.error(f"Error getting progress: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


def reset_command(args):
    """Reset chunks to pending status."""
    session = SessionLocal()
    chunk_manager = CSVChunkManager()

    try:
        logger.info(f"Resetting chunks for {args.table} ({args.date})...")

        count = chunk_manager.reset_chunks(
            table_name=args.table,
            dataset_date=args.date,
            db_session=session
        )

        logger.info(f"✓ Reset {count} chunks to pending status")

    except Exception as e:
        logger.error(f"Error resetting chunks: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


def delete_command(args):
    """Delete chunks and optionally files."""
    session = SessionLocal()
    chunk_manager = CSVChunkManager()

    try:
        logger.info(f"Deleting chunks for {args.table} ({args.date})...")
        if args.delete_files:
            logger.warning("This will also delete chunk files from disk!")

        if not args.yes:
            response = input("Are you sure? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Cancelled")
                sys.exit(0)

        count = chunk_manager.delete_chunks(
            table_name=args.table,
            dataset_date=args.date,
            delete_files=args.delete_files,
            db_session=session
        )

        logger.info(f"✓ Deleted {count} chunk records" +
                   (" and files" if args.delete_files else ""))

    except Exception as e:
        logger.error(f"Error deleting chunks: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Chunk and import large CSV files for CourtListener database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Chunk command
    chunk_parser = subparsers.add_parser("chunk", help="Chunk a CSV file")
    chunk_parser.add_argument("--table", required=True, help="Table name (e.g., search_docket)")
    chunk_parser.add_argument("--date", required=True, help="Dataset date (YYYY-MM-DD)")
    chunk_parser.add_argument("--chunk-size", type=int, default=1_000_000,
                             help="Rows per chunk (default: 1,000,000)")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import chunks")
    import_parser.add_argument("--table", required=True, help="Table name")
    import_parser.add_argument("--date", required=True, help="Dataset date (YYYY-MM-DD)")
    import_parser.add_argument("--method", choices=["standard", "pandas", "copy"],
                              default="standard", help="Import method (default: standard)")
    import_parser.add_argument("--no-resume", dest="resume", action="store_false",
                              help="Don't resume from last successful chunk")
    import_parser.add_argument("--max-retries", type=int, default=3,
                              help="Max retry attempts per chunk (default: 3)")

    # Progress command
    progress_parser = subparsers.add_parser("progress", help="Show import progress")
    progress_parser.add_argument("--table", required=True, help="Table name")
    progress_parser.add_argument("--date", required=True, help="Dataset date (YYYY-MM-DD)")
    progress_parser.add_argument("--detailed", action="store_true",
                                help="Show detailed chunk status")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset chunks to pending")
    reset_parser.add_argument("--table", required=True, help="Table name")
    reset_parser.add_argument("--date", required=True, help="Dataset date (YYYY-MM-DD)")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete chunks")
    delete_parser.add_argument("--table", required=True, help="Table name")
    delete_parser.add_argument("--date", required=True, help="Dataset date (YYYY-MM-DD)")
    delete_parser.add_argument("--delete-files", action="store_true",
                              help="Also delete chunk files from disk")
    delete_parser.add_argument("--yes", action="store_true",
                              help="Skip confirmation prompt")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command handler
    if args.command == "chunk":
        chunk_command(args)
    elif args.command == "import":
        import_command(args)
    elif args.command == "progress":
        progress_command(args)
    elif args.command == "reset":
        reset_command(args)
    elif args.command == "delete":
        delete_command(args)


if __name__ == "__main__":
    main()
