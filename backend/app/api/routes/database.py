"""
Database Import/Export API Routes

Endpoints for uploading and restoring PostgreSQL dumps
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import subprocess
import os
from pathlib import Path
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

DUMP_DIR = Path("/app/dumps")
DUMP_DIR.mkdir(exist_ok=True)


@router.post("/upload-dump")
async def upload_dump(file: UploadFile = File(...)):
    """
    Upload a PostgreSQL dump file for restoration.
    Accepts pg_dump custom format (.pgdump) files.
    """
    try:
        # Validate file extension
        if not file.filename.endswith(('.pgdump', '.dump', '.sql')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Expected .pgdump, .dump, or .sql file"
            )

        # Save the uploaded file
        dump_path = DUMP_DIR / file.filename

        logger.info(f"Receiving dump file: {file.filename}")

        with open(dump_path, "wb") as buffer:
            chunk_size = 10 * 1024 * 1024  # 10MB chunks
            while chunk := await file.read(chunk_size):
                buffer.write(chunk)

        file_size_mb = dump_path.stat().st_size / (1024 * 1024)
        logger.info(f"Dump file saved: {dump_path} ({file_size_mb:.2f} MB)")

        return {
            "status": "success",
            "filename": file.filename,
            "size_mb": round(file_size_mb, 2),
            "path": str(dump_path)
        }

    except Exception as e:
        logger.error(f"Error uploading dump: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restore-dump")
async def restore_dump(filename: str, background_tasks: BackgroundTasks):
    """
    Restore a previously uploaded PostgreSQL dump file.
    This runs in the background and returns immediately.
    """
    try:
        dump_path = DUMP_DIR / filename

        if not dump_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Dump file not found: {filename}"
            )

        # Add the restore task to background
        background_tasks.add_task(restore_dump_task, dump_path)

        return {
            "status": "started",
            "message": f"Restore of {filename} started in background",
            "filename": filename
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting restore: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def restore_dump_task(dump_path: Path):
    """
    Background task to restore the PostgreSQL dump.
    """
    try:
        logger.info(f"Starting restore from: {dump_path}")

        # Get database connection details from environment
        db_host = os.getenv("DATABASE_HOST", "localhost")
        db_port = os.getenv("DATABASE_PORT", "5432")
        db_user = os.getenv("DATABASE_USER", "postgres")
        db_name = os.getenv("DATABASE_NAME", "railway")
        db_pass = os.getenv("DATABASE_PASSWORD", "")

        # Set PGPASSWORD environment variable for pg_restore
        env = os.environ.copy()
        env["PGPASSWORD"] = db_pass

        # Build pg_restore command
        cmd = [
            "pg_restore",
            "--verbose",
            "--no-owner",
            "--no-privileges",
            "--no-tablespaces",
            "-h", db_host,
            "-p", db_port,
            "-U", db_user,
            "-d", db_name,
            str(dump_path)
        ]

        logger.info(f"Running pg_restore command (host={db_host}, db={db_name})")

        # Run pg_restore
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        if result.returncode == 0:
            logger.info(f"✓ Restore completed successfully from {dump_path}")
        else:
            logger.error(f"Restore failed with code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"Restore timed out after 1 hour")
    except Exception as e:
        logger.error(f"Error during restore: {e}")


@router.get("/restore-status")
async def get_restore_status():
    """
    Get the current status of database restoration.
    Checks if pg_restore process is running.
    """
    try:
        # Check if pg_restore is running
        result = subprocess.run(
            ["pgrep", "-f", "pg_restore"],
            capture_output=True,
            text=True
        )

        is_running = result.returncode == 0

        return {
            "restore_in_progress": is_running,
            "status": "restoring" if is_running else "idle"
        }

    except Exception as e:
        logger.error(f"Error checking restore status: {e}")
        return {
            "restore_in_progress": False,
            "status": "unknown",
            "error": str(e)
        }


@router.get("/dumps")
async def list_dumps():
    """
    List all available dump files on the server.
    """
    try:
        dumps = []
        for dump_file in DUMP_DIR.glob("*"):
            if dump_file.is_file():
                size_mb = dump_file.stat().st_size / (1024 * 1024)
                dumps.append({
                    "filename": dump_file.name,
                    "size_mb": round(size_mb, 2),
                    "modified": dump_file.stat().st_mtime
                })

        dumps.sort(key=lambda x: x["modified"], reverse=True)

        return {
            "dumps": dumps,
            "count": len(dumps)
        }

    except Exception as e:
        logger.error(f"Error listing dumps: {e}")
        raise HTTPException(status_code=500, detail=str(e))
