"""
CSV Chunk Manager Service

Handles chunking of large CSV files and tracking import progress.
Enables safe, resumable imports of massive datasets.
"""
import csv
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.csv_chunk_progress import CSVChunkProgress
from app.services.data_importer import DataImporter

logger = logging.getLogger(__name__)


class CSVChunkManager:
    """
    Manager for chunking large CSV files and tracking import progress.

    Features:
    - Split large CSVs into manageable chunks
    - Track progress per chunk in database
    - Resume imports from last successful chunk
    - Detailed error tracking and retry logic
    - Works with existing import methods
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize CSV chunk manager.

        Args:
            data_dir: Directory containing CSV files. Defaults to settings.DATA_DIR
        """
        self.data_dir = Path(data_dir) if data_dir else Path(settings.DATA_DIR)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chunks_dir = self.data_dir / "chunks"
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        self.importer = DataImporter(data_dir=self.data_dir)

    def chunk_csv(
        self,
        csv_path: Path,
        table_name: str,
        dataset_date: str,
        chunk_size: int = 1_000_000,
        db_session: Optional[Session] = None
    ) -> List[Path]:
        """
        Split a large CSV file into numbered chunks.

        Args:
            csv_path: Path to the source CSV file
            table_name: Name of the target database table
            dataset_date: Date string (YYYY-MM-DD) for the dataset
            chunk_size: Number of rows per chunk (default 1M)
            db_session: Optional database session for progress tracking

        Returns:
            List of paths to created chunk files
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        logger.info(f"=" * 80)
        logger.info(f"Chunking CSV: {csv_path.name}")
        logger.info(f"Table: {table_name}")
        logger.info(f"Chunk size: {chunk_size:,} rows")
        logger.info(f"=" * 80)

        # Increase CSV field size limit for large fields
        maxInt = sys.maxsize
        while True:
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt / 10)

        # Create chunk directory for this table/date
        chunk_subdir = self.chunks_dir / f"{table_name}-{dataset_date}"
        chunk_subdir.mkdir(parents=True, exist_ok=True)

        chunk_files = []
        chunk_num = 0
        current_chunk_rows = []
        total_rows = 0
        header = None

        try:
            with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                csv_reader = csv.reader(f, quoting=csv.QUOTE_MINIMAL)

                # Read and save header
                header = next(csv_reader)

                for row in csv_reader:
                    total_rows += 1
                    current_chunk_rows.append(row)

                    # Write chunk when it reaches chunk_size
                    if len(current_chunk_rows) >= chunk_size:
                        chunk_num += 1
                        chunk_file = self._write_chunk(
                            chunk_subdir=chunk_subdir,
                            table_name=table_name,
                            dataset_date=dataset_date,
                            chunk_num=chunk_num,
                            header=header,
                            rows=current_chunk_rows,
                            start_row=total_rows - len(current_chunk_rows) + 1,
                            end_row=total_rows
                        )
                        chunk_files.append(chunk_file)

                        # Track in database if session provided
                        if db_session:
                            self._create_chunk_progress_record(
                                session=db_session,
                                table_name=table_name,
                                dataset_date=dataset_date,
                                chunk_number=chunk_num,
                                chunk_filename=chunk_file.name,
                                start_row=total_rows - len(current_chunk_rows) + 1,
                                end_row=total_rows,
                                row_count=len(current_chunk_rows)
                            )

                        logger.info(f"Created chunk {chunk_num}: {chunk_file.name} ({len(current_chunk_rows):,} rows)")
                        current_chunk_rows = []

                # Write remaining rows as final chunk
                if current_chunk_rows:
                    chunk_num += 1
                    chunk_file = self._write_chunk(
                        chunk_subdir=chunk_subdir,
                        table_name=table_name,
                        dataset_date=dataset_date,
                        chunk_num=chunk_num,
                        header=header,
                        rows=current_chunk_rows,
                        start_row=total_rows - len(current_chunk_rows) + 1,
                        end_row=total_rows
                    )
                    chunk_files.append(chunk_file)

                    if db_session:
                        self._create_chunk_progress_record(
                            session=db_session,
                            table_name=table_name,
                            dataset_date=dataset_date,
                            chunk_number=chunk_num,
                            chunk_filename=chunk_file.name,
                            start_row=total_rows - len(current_chunk_rows) + 1,
                            end_row=total_rows,
                            row_count=len(current_chunk_rows)
                        )

                    logger.info(f"Created final chunk {chunk_num}: {chunk_file.name} ({len(current_chunk_rows):,} rows)")

            if db_session:
                db_session.commit()

            logger.info(f"=" * 80)
            logger.info(f"Chunking complete!")
            logger.info(f"Total rows: {total_rows:,}")
            logger.info(f"Total chunks: {chunk_num}")
            logger.info(f"Chunk directory: {chunk_subdir}")
            logger.info(f"=" * 80)

            return chunk_files

        except Exception as e:
            logger.error(f"Error chunking CSV: {str(e)}")
            if db_session:
                db_session.rollback()
            raise

    def _write_chunk(
        self,
        chunk_subdir: Path,
        table_name: str,
        dataset_date: str,
        chunk_num: int,
        header: List[str],
        rows: List[List[str]],
        start_row: int,
        end_row: int
    ) -> Path:
        """Write a chunk to a CSV file."""
        chunk_filename = f"{table_name}-{dataset_date}.chunk_{chunk_num:04d}.csv"
        chunk_path = chunk_subdir / chunk_filename

        with open(chunk_path, 'w', encoding='utf-8', newline='') as f:
            csv_writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header)
            csv_writer.writerows(rows)

        return chunk_path

    def _create_chunk_progress_record(
        self,
        session: Session,
        table_name: str,
        dataset_date: str,
        chunk_number: int,
        chunk_filename: str,
        start_row: int,
        end_row: int,
        row_count: int
    ):
        """Create a progress tracking record for a chunk."""
        chunk_progress = CSVChunkProgress(
            table_name=table_name,
            dataset_date=dataset_date,
            chunk_number=chunk_number,
            chunk_filename=chunk_filename,
            chunk_start_row=start_row,
            chunk_end_row=end_row,
            chunk_row_count=row_count,
            status="pending"
        )
        session.add(chunk_progress)

    def get_chunks(
        self,
        table_name: str,
        dataset_date: str,
        db_session: Optional[Session] = None
    ) -> List[Dict]:
        """
        Get list of chunks for a table/date with their progress status.

        Args:
            table_name: Name of the table
            dataset_date: Date string (YYYY-MM-DD)
            db_session: Optional database session

        Returns:
            List of chunk dictionaries with status information
        """
        should_close = False
        if db_session:
            session = db_session
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            chunks = session.query(CSVChunkProgress).filter(
                CSVChunkProgress.table_name == table_name,
                CSVChunkProgress.dataset_date == dataset_date
            ).order_by(CSVChunkProgress.chunk_number).all()

            return [
                {
                    "chunk_number": c.chunk_number,
                    "chunk_filename": c.chunk_filename,
                    "status": c.status,
                    "chunk_row_count": c.chunk_row_count,
                    "rows_imported": c.rows_imported,
                    "rows_skipped": c.rows_skipped,
                    "duration_seconds": c.duration_seconds,
                    "error_message": c.error_message,
                    "started_at": c.started_at.isoformat() if c.started_at else None,
                    "completed_at": c.completed_at.isoformat() if c.completed_at else None,
                }
                for c in chunks
            ]
        finally:
            if should_close:
                session.close()

    def get_progress_summary(
        self,
        table_name: str,
        dataset_date: str,
        db_session: Optional[Session] = None
    ) -> Dict:
        """
        Get overall progress summary for a chunked import.

        Args:
            table_name: Name of the table
            dataset_date: Date string (YYYY-MM-DD)
            db_session: Optional database session

        Returns:
            Dictionary with progress statistics
        """
        should_close = False
        if db_session:
            session = db_session
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            chunks = session.query(CSVChunkProgress).filter(
                CSVChunkProgress.table_name == table_name,
                CSVChunkProgress.dataset_date == dataset_date
            ).all()

            if not chunks:
                return {
                    "table_name": table_name,
                    "dataset_date": dataset_date,
                    "total_chunks": 0,
                    "status": "not_started"
                }

            total_chunks = len(chunks)
            completed = sum(1 for c in chunks if c.status == "completed")
            failed = sum(1 for c in chunks if c.status == "failed")
            processing = sum(1 for c in chunks if c.status == "processing")
            pending = sum(1 for c in chunks if c.status == "pending")

            total_rows = sum(c.chunk_row_count or 0 for c in chunks)
            imported_rows = sum(c.rows_imported or 0 for c in chunks)
            skipped_rows = sum(c.rows_skipped or 0 for c in chunks)

            # Calculate overall status
            if completed == total_chunks:
                overall_status = "completed"
            elif failed > 0:
                overall_status = "failed"
            elif processing > 0:
                overall_status = "processing"
            elif pending > 0 and completed > 0:
                overall_status = "in_progress"
            else:
                overall_status = "pending"

            return {
                "table_name": table_name,
                "dataset_date": dataset_date,
                "total_chunks": total_chunks,
                "completed_chunks": completed,
                "failed_chunks": failed,
                "processing_chunks": processing,
                "pending_chunks": pending,
                "total_rows": total_rows,
                "imported_rows": imported_rows,
                "skipped_rows": skipped_rows,
                "progress_percentage": (completed / total_chunks * 100) if total_chunks > 0 else 0,
                "status": overall_status
            }
        finally:
            if should_close:
                session.close()

    def import_chunked(
        self,
        table_name: str,
        dataset_date: str,
        import_method: str = "standard",
        resume: bool = True,
        max_retries: int = 3,
        db_session: Optional[Session] = None
    ) -> Dict:
        """
        Import all chunks for a table sequentially with progress tracking.

        Args:
            table_name: Name of the table to import into
            dataset_date: Date string (YYYY-MM-DD) for the dataset
            import_method: Import method to use ("standard", "pandas", "copy")
            resume: If True, skip already completed chunks
            max_retries: Maximum retry attempts for failed chunks
            db_session: Optional database session

        Returns:
            Dictionary with import results and statistics
        """
        should_close = False
        if db_session:
            session = db_session
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            logger.info(f"=" * 80)
            logger.info(f"Starting chunked import: {table_name}")
            logger.info(f"Dataset date: {dataset_date}")
            logger.info(f"Import method: {import_method}")
            logger.info(f"Resume mode: {resume}")
            logger.info(f"=" * 80)

            # Get all chunks for this table/date
            chunk_records = session.query(CSVChunkProgress).filter(
                CSVChunkProgress.table_name == table_name,
                CSVChunkProgress.dataset_date == dataset_date
            ).order_by(CSVChunkProgress.chunk_number).all()

            if not chunk_records:
                raise ValueError(f"No chunks found for {table_name} on {dataset_date}. Run chunk_csv() first.")

            total_chunks = len(chunk_records)
            logger.info(f"Found {total_chunks} chunks to process")

            # Filter chunks to process
            if resume:
                chunks_to_process = [c for c in chunk_records if c.status != "completed"]
                skipped_count = total_chunks - len(chunks_to_process)
                if skipped_count > 0:
                    logger.info(f"Skipping {skipped_count} already completed chunks (resume mode)")
            else:
                chunks_to_process = chunk_records

            # Import each chunk
            results = {
                "table_name": table_name,
                "dataset_date": dataset_date,
                "total_chunks": total_chunks,
                "processed_chunks": 0,
                "successful_chunks": 0,
                "failed_chunks": 0,
                "skipped_chunks": skipped_count if resume else 0,
                "total_rows_imported": 0,
                "total_rows_skipped": 0,
                "import_method": import_method,
                "errors": []
            }

            chunk_subdir = self.chunks_dir / f"{table_name}-{dataset_date}"

            for chunk_record in chunks_to_process:
                chunk_path = chunk_subdir / chunk_record.chunk_filename

                if not chunk_path.exists():
                    error_msg = f"Chunk file not found: {chunk_path}"
                    logger.error(error_msg)
                    self._mark_chunk_failed(session, chunk_record, error_msg)
                    results["failed_chunks"] += 1
                    results["errors"].append({"chunk": chunk_record.chunk_number, "error": error_msg})
                    continue

                # Process chunk with retry logic
                success = False
                for attempt in range(max_retries):
                    try:
                        logger.info(f"\n{'='*60}")
                        logger.info(f"Processing chunk {chunk_record.chunk_number}/{total_chunks}")
                        logger.info(f"File: {chunk_record.chunk_filename}")
                        logger.info(f"Attempt: {attempt + 1}/{max_retries}")
                        logger.info(f"{'='*60}")

                        # Mark as processing
                        chunk_record.status = "processing"
                        chunk_record.started_at = datetime.now(timezone.utc)
                        chunk_record.import_method = import_method
                        chunk_record.retry_count = attempt
                        session.commit()

                        # Import chunk using specified method
                        start_time = datetime.now(timezone.utc)

                        if import_method == "pandas":
                            rows_imported = self.importer.import_csv_pandas(
                                table_name=table_name,
                                csv_path=chunk_path,
                                db_session=session
                            )
                        elif import_method == "copy":
                            rows_imported = self.importer.import_csv_with_postgres_copy(
                                table_name=table_name,
                                csv_path=chunk_path,
                                db_session=session
                            )
                        else:  # standard
                            rows_imported = self.importer.import_csv(
                                table_name=table_name,
                                csv_path=chunk_path,
                                db_session=session
                            )

                        end_time = datetime.now(timezone.utc)
                        duration = (end_time - start_time).total_seconds()

                        # Mark as completed
                        chunk_record.status = "completed"
                        chunk_record.completed_at = end_time
                        chunk_record.duration_seconds = int(duration)
                        chunk_record.rows_imported = rows_imported
                        chunk_record.error_message = None
                        session.commit()

                        results["successful_chunks"] += 1
                        results["total_rows_imported"] += rows_imported

                        logger.info(f"✓ Chunk {chunk_record.chunk_number} completed: {rows_imported:,} rows in {duration:.1f}s")
                        success = True
                        break

                    except Exception as e:
                        error_msg = str(e)[:500]  # Limit error message length
                        logger.error(f"✗ Chunk {chunk_record.chunk_number} failed (attempt {attempt + 1}): {error_msg}")

                        if attempt == max_retries - 1:
                            # Final attempt failed
                            self._mark_chunk_failed(session, chunk_record, error_msg)
                            results["failed_chunks"] += 1
                            results["errors"].append({
                                "chunk": chunk_record.chunk_number,
                                "error": error_msg,
                                "attempts": max_retries
                            })
                        else:
                            # Retry
                            session.rollback()
                            logger.info(f"Retrying chunk {chunk_record.chunk_number}...")

                results["processed_chunks"] += 1

            # Final summary
            logger.info(f"\n" + "=" * 80)
            logger.info(f"Chunked import complete: {table_name}")
            logger.info(f"Total chunks: {total_chunks}")
            logger.info(f"Successful: {results['successful_chunks']}")
            logger.info(f"Failed: {results['failed_chunks']}")
            logger.info(f"Skipped: {results['skipped_chunks']}")
            logger.info(f"Total rows imported: {results['total_rows_imported']:,}")
            logger.info(f"=" * 80)

            return results

        finally:
            if should_close:
                session.close()

    def _mark_chunk_failed(self, session: Session, chunk_record: CSVChunkProgress, error_msg: str):
        """Mark a chunk as failed with error message."""
        chunk_record.status = "failed"
        chunk_record.completed_at = datetime.now(timezone.utc)
        chunk_record.error_message = error_msg
        session.commit()

    def reset_chunks(
        self,
        table_name: str,
        dataset_date: str,
        db_session: Optional[Session] = None
    ) -> int:
        """
        Reset all chunks to pending status (for re-import).

        Args:
            table_name: Name of the table
            dataset_date: Date string (YYYY-MM-DD)
            db_session: Optional database session

        Returns:
            Number of chunks reset
        """
        should_close = False
        if db_session:
            session = db_session
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            chunks = session.query(CSVChunkProgress).filter(
                CSVChunkProgress.table_name == table_name,
                CSVChunkProgress.dataset_date == dataset_date
            ).all()

            for chunk in chunks:
                chunk.status = "pending"
                chunk.started_at = None
                chunk.completed_at = None
                chunk.duration_seconds = None
                chunk.rows_imported = 0
                chunk.rows_skipped = 0
                chunk.error_message = None
                chunk.retry_count = 0

            session.commit()

            logger.info(f"Reset {len(chunks)} chunks for {table_name} ({dataset_date}) to pending status")
            return len(chunks)

        finally:
            if should_close:
                session.close()

    def delete_chunks(
        self,
        table_name: str,
        dataset_date: str,
        delete_files: bool = True,
        db_session: Optional[Session] = None
    ) -> int:
        """
        Delete chunk records and optionally chunk files.

        Args:
            table_name: Name of the table
            dataset_date: Date string (YYYY-MM-DD)
            delete_files: If True, also delete chunk files from disk
            db_session: Optional database session

        Returns:
            Number of chunks deleted
        """
        should_close = False
        if db_session:
            session = db_session
        else:
            from app.core.database import SessionLocal
            session = SessionLocal()
            should_close = True

        try:
            chunks = session.query(CSVChunkProgress).filter(
                CSVChunkProgress.table_name == table_name,
                CSVChunkProgress.dataset_date == dataset_date
            ).all()

            count = len(chunks)

            # Delete files if requested
            if delete_files:
                chunk_subdir = self.chunks_dir / f"{table_name}-{dataset_date}"
                if chunk_subdir.exists():
                    for chunk in chunks:
                        chunk_file = chunk_subdir / chunk.chunk_filename
                        if chunk_file.exists():
                            chunk_file.unlink()

                    # Remove directory if empty
                    try:
                        chunk_subdir.rmdir()
                    except OSError:
                        pass  # Directory not empty

            # Delete database records
            for chunk in chunks:
                session.delete(chunk)

            session.commit()

            logger.info(f"Deleted {count} chunk records for {table_name} ({dataset_date})")
            return count

        finally:
            if should_close:
                session.close()
