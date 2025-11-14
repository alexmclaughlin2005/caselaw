"""
File Upload API Routes

Endpoints for uploading CSV files to the Railway volume.
"""
from fastapi import APIRouter, File, UploadFile, HTTPException
from pathlib import Path
import shutil
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload-csv")
async def upload_csv_file(file: UploadFile = File(...)):
    """
    Upload a CSV file to the data directory on Railway.

    This endpoint allows uploading large CSV files directly to Railway's volume
    without requiring Railway CLI or shell access.

    Args:
        file: The CSV file to upload

    Returns:
        Dictionary with upload status and file information
    """
    try:
        # Validate file extension
        if not file.filename.endswith('.csv'):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Only .csv files are allowed. Got: {file.filename}"
            )

        # Construct target path
        data_dir = Path(settings.DATA_DIR)
        data_dir.mkdir(parents=True, exist_ok=True)

        target_path = data_dir / file.filename

        # Write file in chunks to handle large files
        logger.info(f"[UPLOAD] Starting upload: {file.filename}")

        with open(target_path, 'wb') as buffer:
            chunk_size = 1024 * 1024  # 1MB chunks
            bytes_written = 0

            while chunk := await file.read(chunk_size):
                buffer.write(chunk)
                bytes_written += len(chunk)

                # Log progress every 100MB
                if bytes_written % (100 * 1024 * 1024) == 0:
                    logger.info(f"[UPLOAD] Progress: {bytes_written / (1024**3):.2f} GB")

        file_size_gb = target_path.stat().st_size / (1024**3)
        logger.info(f"[UPLOAD] Complete: {file.filename} ({file_size_gb:.2f} GB)")

        return {
            "status": "success",
            "filename": file.filename,
            "path": str(target_path),
            "size_gb": round(file_size_gb, 2),
            "message": f"File uploaded successfully: {file.filename}"
        }

    except Exception as e:
        logger.error(f"[UPLOAD] Error uploading {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-csv-files")
async def list_csv_files():
    """
    List all CSV files in the data directory.

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
        for csv_file in data_dir.glob("*.csv"):
            file_size_gb = csv_file.stat().st_size / (1024**3)
            csv_files.append({
                "filename": csv_file.name,
                "path": str(csv_file),
                "size_gb": round(file_size_gb, 2)
            })

        csv_files.sort(key=lambda x: x["filename"])

        return {
            "status": "success",
            "count": len(csv_files),
            "files": csv_files,
            "data_directory": str(data_dir)
        }

    except Exception as e:
        logger.error(f"[LIST] Error listing CSV files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
