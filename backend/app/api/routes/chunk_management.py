"""
Chunk Management API Routes

Endpoints for chunking large CSV files and managing chunked imports.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path
import logging
import asyncio
import os

from app.api.deps import get_db
from app.schemas.data_management import (
    ChunkRequest,
    ChunkListResponse,
    ChunkInfo,
    ChunkProgressSummary,
    ChunkedImportRequest,
    ChunkedImportResponse,
    ChunkResetRequest,
    ChunkDeleteRequest,
)
from app.services.csv_chunk_manager import CSVChunkManager
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize chunk manager
chunk_manager = CSVChunkManager()


async def check_file_exists_async(file_path: Path, timeout: int = 5) -> bool:
    """
    Check if file exists with timeout to prevent hanging on slow I/O.

    Args:
        file_path: Path to check
        timeout: Timeout in seconds (default 5)

    Returns:
        True if file exists, False otherwise

    Raises:
        TimeoutError: If check takes longer than timeout
    """
    def _check():
        return os.path.exists(str(file_path))

    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _check),
            timeout=timeout
        )
        return result
    except asyncio.TimeoutError:
        raise TimeoutError(f"File existence check timed out after {timeout}s for: {file_path}")


@router.post("/chunk", response_model=ChunkListResponse)
async def create_chunks(
    request: ChunkRequest,
    db: Session = Depends(get_db)
):
    """
    Split a large CSV file into numbered chunks for sequential import.

    This endpoint chunks a CSV file on disk and creates progress tracking
    records in the database. The original file is preserved.

    Args:
        request: ChunkRequest with table name, date, filename, and chunk size

    Returns:
        ChunkListResponse with information about created chunks
    """
    try:
        logger.info(f"[CHUNK REQUEST] Received request for {request.table_name} - {request.csv_filename}")

        # Construct CSV path
        csv_path = Path(settings.DATA_DIR) / request.csv_filename
        logger.info(f"[CHUNK REQUEST] Checking file existence: {csv_path}")

        # Check file exists with timeout to prevent hanging
        try:
            file_exists = await check_file_exists_async(csv_path, timeout=5)
        except TimeoutError as e:
            logger.error(f"[CHUNK REQUEST] File check timed out: {str(e)}")
            raise HTTPException(
                status_code=504,
                detail=f"File system timeout while checking for {request.csv_filename}. "
                       f"Railway volume may be experiencing I/O issues."
            )

        if not file_exists:
            logger.warning(f"[CHUNK REQUEST] File not found: {csv_path}")
            raise HTTPException(
                status_code=404,
                detail=f"CSV file not found: {request.csv_filename}"
            )

        logger.info(f"[CHUNK REQUEST] File found, starting chunking for {request.table_name}")

        # Create chunks (this is blocking - run in executor)
        loop = asyncio.get_event_loop()
        chunk_files = await loop.run_in_executor(
            None,
            chunk_manager.chunk_csv,
            csv_path,
            request.table_name,
            request.dataset_date,
            request.chunk_size,
            db
        )

        logger.info(f"[CHUNK REQUEST] Created {len(chunk_files)} chunks")

        # Get chunk information
        chunks = chunk_manager.get_chunks(
            table_name=request.table_name,
            dataset_date=request.dataset_date,
            db_session=db
        )

        logger.info(f"[CHUNK REQUEST] Returning {len(chunks)} chunk records")

        return ChunkListResponse(
            table_name=request.table_name,
            dataset_date=request.dataset_date,
            chunks=[ChunkInfo(**chunk) for chunk in chunks],
            total_chunks=len(chunks)
        )

    except HTTPException:
        raise
    except FileNotFoundError as e:
        logger.error(f"[CHUNK REQUEST] File not found error: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"[CHUNK REQUEST] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/{table_name}/{dataset_date}", response_model=ChunkListResponse)
async def list_chunks(
    table_name: str,
    dataset_date: str,
    db: Session = Depends(get_db)
):
    """
    Get list of all chunks for a table/date with their status.

    Args:
        table_name: Name of the database table
        dataset_date: Date string (YYYY-MM-DD)

    Returns:
        ChunkListResponse with chunk information
    """
    try:
        chunks = chunk_manager.get_chunks(
            table_name=table_name,
            dataset_date=dataset_date,
            db_session=db
        )

        return ChunkListResponse(
            table_name=table_name,
            dataset_date=dataset_date,
            chunks=[ChunkInfo(**chunk) for chunk in chunks],
            total_chunks=len(chunks)
        )

    except Exception as e:
        logger.error(f"Error listing chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chunks/{table_name}/{dataset_date}/progress", response_model=ChunkProgressSummary)
async def get_chunk_progress(
    table_name: str,
    dataset_date: str,
    db: Session = Depends(get_db)
):
    """
    Get progress summary for a chunked import.

    Provides aggregate statistics including completion percentage,
    total rows processed, and overall status.

    Args:
        table_name: Name of the database table
        dataset_date: Date string (YYYY-MM-DD)

    Returns:
        ChunkProgressSummary with aggregate statistics
    """
    try:
        summary = chunk_manager.get_progress_summary(
            table_name=table_name,
            dataset_date=dataset_date,
            db_session=db
        )

        return ChunkProgressSummary(**summary)

    except Exception as e:
        logger.error(f"Error getting chunk progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chunks/import", response_model=ChunkedImportResponse)
async def import_chunks(
    request: ChunkedImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Import all chunks for a table sequentially with progress tracking.

    This endpoint processes chunks in order, tracking progress per chunk.
    Supports resume mode to skip already completed chunks, and automatic
    retry logic for failed chunks.

    Note: This is a synchronous operation that may take a long time for
    large datasets. Consider using background tasks in production.

    Args:
        request: ChunkedImportRequest with import parameters

    Returns:
        ChunkedImportResponse with import results
    """
    try:
        logger.info(f"Starting chunked import for {request.table_name} ({request.dataset_date})")

        # Validate import method
        valid_methods = ["standard", "pandas", "copy"]
        if request.import_method not in valid_methods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid import method. Must be one of: {valid_methods}"
            )

        # Check if chunks exist
        chunks = chunk_manager.get_chunks(
            table_name=request.table_name,
            dataset_date=request.dataset_date,
            db_session=db
        )

        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"No chunks found for {request.table_name} on {request.dataset_date}. "
                       f"Create chunks first using POST /api/chunks/chunk"
            )

        # Start import
        results = chunk_manager.import_chunked(
            table_name=request.table_name,
            dataset_date=request.dataset_date,
            import_method=request.import_method,
            resume=request.resume,
            max_retries=request.max_retries,
            db_session=db
        )

        # Determine overall status
        if results["failed_chunks"] == 0:
            status = "completed"
        elif results["successful_chunks"] > 0:
            status = "partial"
        else:
            status = "failed"

        return ChunkedImportResponse(
            table_name=results["table_name"],
            dataset_date=results["dataset_date"],
            total_chunks=results["total_chunks"],
            processed_chunks=results["processed_chunks"],
            successful_chunks=results["successful_chunks"],
            failed_chunks=results["failed_chunks"],
            skipped_chunks=results["skipped_chunks"],
            total_rows_imported=results["total_rows_imported"],
            total_rows_skipped=results["total_rows_skipped"],
            import_method=results["import_method"],
            errors=results["errors"],
            status=status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during chunked import: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chunks/reset")
async def reset_chunks(
    request: ChunkResetRequest,
    db: Session = Depends(get_db)
):
    """
    Reset all chunks to pending status for re-import.

    This clears all progress tracking information but preserves the
    chunk files on disk.

    Args:
        request: ChunkResetRequest with table name and dataset date

    Returns:
        Dictionary with number of chunks reset
    """
    try:
        count = chunk_manager.reset_chunks(
            table_name=request.table_name,
            dataset_date=request.dataset_date,
            db_session=db
        )

        return {
            "table_name": request.table_name,
            "dataset_date": request.dataset_date,
            "chunks_reset": count,
            "message": f"Reset {count} chunks to pending status"
        }

    except Exception as e:
        logger.error(f"Error resetting chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chunks")
async def delete_chunks(
    request: ChunkDeleteRequest,
    db: Session = Depends(get_db)
):
    """
    Delete chunk records and optionally chunk files.

    Args:
        request: ChunkDeleteRequest with table name, date, and delete_files flag

    Returns:
        Dictionary with number of chunks deleted
    """
    try:
        count = chunk_manager.delete_chunks(
            table_name=request.table_name,
            dataset_date=request.dataset_date,
            delete_files=request.delete_files,
            db_session=db
        )

        return {
            "table_name": request.table_name,
            "dataset_date": request.dataset_date,
            "chunks_deleted": count,
            "files_deleted": request.delete_files,
            "message": f"Deleted {count} chunk records" +
                      (f" and files" if request.delete_files else "")
        }

    except Exception as e:
        logger.error(f"Error deleting chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
