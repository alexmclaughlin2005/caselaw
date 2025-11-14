"""
Simple Download API Routes

Simple endpoint to download specific CSV files from CourtListener S3.
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
import logging
from app.services.s3_downloader import CourtListenerDownloader
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
downloader = CourtListenerDownloader()


@router.post("/download-file")
async def download_single_file(table_name: str, dataset_date: str = "2025-10-31"):
    """
    Download a single CSV file from CourtListener S3 to Railway volume.

    This endpoint downloads files directly from S3, which is much faster than
    uploading from a local machine.

    Args:
        table_name: Name of the table (e.g., "search_docket", "search_opinioncluster")
        dataset_date: Date string (default "2025-10-31")

    Returns:
        Dictionary with download status and file information
    """
    try:
        # Mapping of table names to S3 file names
        table_to_s3_file = {
            "search_docket": f"dockets-{dataset_date}.csv.bz2",
            "search_opinioncluster": f"opinion-clusters-{dataset_date}.csv.bz2",
            "search_opinionscited": f"opinions-cited-{dataset_date}.csv.bz2",
            "search_parenthetical": f"parentheticals-{dataset_date}.csv.bz2",
        }

        if table_name not in table_to_s3_file:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid table name. Must be one of: {list(table_to_s3_file.keys())}"
            )

        s3_file = table_to_s3_file[table_name]

        # Construct target path
        data_dir = Path(settings.DATA_DIR)
        data_dir.mkdir(parents=True, exist_ok=True)
        target_path = data_dir / f"{table_name}-{dataset_date}.csv"

        # Check if file already exists
        if target_path.exists():
            file_size_gb = target_path.stat().st_size / (1024**3)
            return {
                "status": "already_exists",
                "table_name": table_name,
                "dataset_date": dataset_date,
                "filename": target_path.name,
                "path": str(target_path),
                "size_gb": round(file_size_gb, 2),
                "message": f"File already exists: {target_path.name}"
            }

        logger.info(f"[DOWNLOAD] Starting download: {s3_file} → {target_path}")

        # Download from S3
        downloaded_path = downloader.download_file(
            key=f"bulk-data/{s3_file}",
            target_path=target_path
        )

        file_size_gb = downloaded_path.stat().st_size / (1024**3)
        logger.info(f"[DOWNLOAD] Complete: {downloaded_path.name} ({file_size_gb:.2f} GB)")

        return {
            "status": "success",
            "table_name": table_name,
            "dataset_date": dataset_date,
            "filename": downloaded_path.name,
            "path": str(downloaded_path),
            "size_gb": round(file_size_gb, 2),
            "message": f"Downloaded successfully: {downloaded_path.name}"
        }

    except Exception as e:
        logger.error(f"[DOWNLOAD] Error downloading {table_name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-files")
async def list_downloaded_files():
    """
    List all CSV files currently on Railway volume.

    Returns:
        Dictionary with list of CSV files and their sizes
    """
    try:
        data_dir = Path(settings.DATA_DIR)

        if not data_dir.exists():
            return {
                "status": "empty",
                "message": "Data directory does not exist yet",
                "files": []
            }

        csv_files = []
        for csv_file in sorted(data_dir.glob("*.csv")):
            file_size_gb = csv_file.stat().st_size / (1024**3)
            csv_files.append({
                "filename": csv_file.name,
                "path": str(csv_file),
                "size_gb": round(file_size_gb, 2)
            })

        return {
            "status": "success",
            "count": len(csv_files),
            "files": csv_files,
            "data_directory": str(data_dir)
        }

    except Exception as e:
        logger.error(f"[LIST] Error listing files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
