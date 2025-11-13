"""
Data Management API Routes

Endpoints for managing data downloads and imports.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from app.api.deps import get_db

logger = logging.getLogger(__name__)
from app.schemas.data_management import (
    AvailableDatasetsResponse,
    DatasetInfo,
    DownloadRequest,
    DownloadStatus,
    DatabaseStatus,
    ImportRequest,
    ImportStatus,
    ImportProgressResponse,
    TableImportProgress,
)
from app.services.s3_downloader import CourtListenerDownloader
from app.services.data_importer import DataImporter
from app.services.data_validator import DataValidator
from app.celery_app import celery_app
from app.tasks.download_tasks import download_dataset_task
from app.tasks.import_tasks import import_dataset_task
from celery.result import AsyncResult
from app.models import Person, Position, School, Education, Docket, OpinionCluster, Citation, Parenthetical
from sqlalchemy import func

router = APIRouter()

# Initialize services
downloader = CourtListenerDownloader()
importer = DataImporter()
validator = DataValidator()

# In-memory task storage (in production, use Redis or database)
download_tasks: dict[str, str] = {}  # Maps date to task_id
import_tasks: dict[str, str] = {}  # Maps date to import task_id


@router.get("/datasets", response_model=AvailableDatasetsResponse)
async def list_available_datasets():
    """
    List all available datasets in the S3 bucket.
    
    Returns information about schema files, CSV files, and import scripts
    available for download.
    """
    try:
        datasets = downloader.list_available_datasets()
        dates = downloader.get_available_dates()
        
        dataset_info = [
            DatasetInfo(**dataset) for dataset in datasets
        ]
        
        return AvailableDatasetsResponse(
            datasets=dataset_info,
            dates=dates
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{date}", response_model=List[DatasetInfo])
async def get_datasets_for_date(date: str):
    """
    Get all files available for a specific date.
    
    Args:
        date: Date string in format YYYY-MM-DD
    """
    try:
        files = downloader.get_files_for_date(date)
        all_files = []
        
        for file_type, file_list in files.items():
            all_files.extend(file_list)
        
        return [DatasetInfo(**f) for f in all_files]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/download", response_model=DownloadStatus)
async def start_download(request: DownloadRequest):
    """
    Start downloading files for a dataset.
    
    This endpoint queues a Celery task for background download processing.
    
    Args:
        request: Download request with date and optional table list
    """
    try:
        # Queue Celery task
        task = download_dataset_task.delay(
            date=request.date,
            tables=request.tables
        )
        
        # Store task ID for status tracking
        download_tasks[request.date] = task.id
        
        return DownloadStatus(
            status="pending",
            date=request.date,
            files={},
            progress=0.0
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/status/{date}", response_model=DownloadStatus)
async def get_download_status(date: str):
    """
    Get the status of a download operation.
    
    Checks Celery task status if a task exists, otherwise checks local files.
    
    Args:
        date: Date string (YYYY-MM-DD)
    """
    # Check if there's an active task
    task_id = download_tasks.get(date)
    
    if task_id:
        task = AsyncResult(task_id, app=celery_app)
        
        if task.state == 'PENDING':
            status = "pending"
            progress = 0.0
            files = {}
        elif task.state == 'PROGRESS':
            status = "downloading"
            meta = task.info if isinstance(task.info, dict) else {}
            progress = meta.get('progress', 0.0) if isinstance(meta, dict) else 0.0
            files = meta.get('files', {}) if isinstance(meta, dict) else {}
        elif task.state == 'SUCCESS':
            status = "completed"
            result = task.result or {}
            progress = 1.0
            # Convert file paths to status dictionaries
            files_raw = result.get('files', {}) if isinstance(result, dict) else {}
            files = {}
            for filename, file_path in files_raw.items():
                if isinstance(file_path, str):
                    # Convert path string to status dict
                    from pathlib import Path
                    path_obj = Path(file_path)
                    files[filename] = {
                        "status": "completed",
                        "exists": path_obj.exists()
                    }
                elif isinstance(file_path, dict):
                    # Already a status dict
                    files[filename] = file_path
            # Remove completed task from tracking
            download_tasks.pop(date, None)
        else:  # FAILURE
            status = "failed"
            meta = task.info if hasattr(task.info, 'get') else {}
            progress = 0.0
            files = {}
            error = meta.get('error', 'Unknown error') if isinstance(meta, dict) else str(task.info)
            return DownloadStatus(
                status=status,
                date=date,
                files=files,
                progress=progress,
                error=error
            )
        
        return DownloadStatus(
            status=status,
            date=date,
            files=files,
            progress=progress
        )
    
    # No active task - check if files exist locally
    files = downloader.get_files_for_date(date)
    
    files_status = {}
    for file_type, file_list in files.items():
        for file_info in file_list:
            filename = file_info['key'].split('/')[-1]
            exists = downloader.file_exists_locally(filename)
            files_status[filename] = {
                "status": "completed" if exists else "pending",
                "exists": exists
            }
    
    return DownloadStatus(
        status="completed" if any(f.get('exists') for f in files_status.values()) else "pending",
        date=date,
        files=files_status,
        progress=1.0 if files_status else 0.0
    )


@router.get("/status", response_model=DatabaseStatus)
async def get_database_status(db: Session = Depends(get_db)):
    """
    Get current database status including record counts and last import info.
    
    Args:
        db: Database session
    """
    try:
        # Get record counts for people database
        total_people = db.query(func.count(Person.id)).scalar() or 0
        total_positions = db.query(func.count(Position.id)).scalar() or 0
        total_schools = db.query(func.count(School.id)).scalar() or 0
        total_educations = db.query(func.count(Education.id)).scalar() or 0

        # Get record counts for case law database
        total_dockets = db.query(func.count(Docket.id)).scalar() or 0
        total_opinion_clusters = db.query(func.count(OpinionCluster.id)).scalar() or 0
        total_citations = db.query(func.count(Citation.id)).scalar() or 0
        total_parentheticals = db.query(func.count(Parenthetical.id)).scalar() or 0

        # Get database size (PostgreSQL specific)
        db_size_result = db.execute(
            func.pg_database_size(func.current_database())
        )
        db_size_bytes = db_size_result.scalar() or 0
        db_size_mb = db_size_bytes / (1024 * 1024) if db_size_bytes else None

        # TODO: Store last import date in a metadata table
        # For now, check if we have any data
        last_import_date = None
        has_data = total_people > 0 or total_dockets > 0
        last_import_status = "no_data" if not has_data else "has_data"

        return DatabaseStatus(
            total_people=total_people,
            total_positions=total_positions,
            total_schools=total_schools,
            total_educations=total_educations,
            total_dockets=total_dockets,
            total_opinion_clusters=total_opinion_clusters,
            total_citations=total_citations,
            total_parentheticals=total_parentheticals,
            last_import_date=last_import_date,
            last_import_status=last_import_status,
            database_size_mb=round(db_size_mb, 2) if db_size_mb else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database status: {str(e)}")


@router.get("/import-progress", response_model=ImportProgressResponse)
async def get_import_progress(db: Session = Depends(get_db)):
    """
    Get real-time import progress for case law tables.

    Returns current row counts for all 4 case law tables to monitor import progress.
    Designed for manual polling by the user.

    Args:
        db: Database session
    """
    try:
        # Expected row counts from CSV files (excluding header row)
        EXPECTED_COUNTS = {
            "search_docket": 69992974,
            "search_opinioncluster": 74582772,
            "search_opinionscited": 75814101,
            "search_parenthetical": 6117877
        }

        # Query current row counts for all case law tables
        docket_count = db.query(func.count(Docket.id)).scalar() or 0
        cluster_count = db.query(func.count(OpinionCluster.id)).scalar() or 0
        citation_count = db.query(func.count(Citation.id)).scalar() or 0
        parenthetical_count = db.query(func.count(Parenthetical.id)).scalar() or 0

        def get_status_and_progress(current: int, expected: int) -> tuple[str, float]:
            """Determine status and progress percentage."""
            if current == 0:
                return "pending", 0.0
            elif current >= expected:
                return "completed", 100.0
            else:
                return "importing", round((current / expected) * 100, 2)

        docket_status, docket_progress = get_status_and_progress(docket_count, EXPECTED_COUNTS["search_docket"])
        cluster_status, cluster_progress = get_status_and_progress(cluster_count, EXPECTED_COUNTS["search_opinioncluster"])
        citation_status, citation_progress = get_status_and_progress(citation_count, EXPECTED_COUNTS["search_opinionscited"])
        parenthetical_status, parenthetical_progress = get_status_and_progress(parenthetical_count, EXPECTED_COUNTS["search_parenthetical"])

        return ImportProgressResponse(
            search_docket=TableImportProgress(
                table_name="search_docket",
                current_count=docket_count,
                expected_count=EXPECTED_COUNTS["search_docket"],
                status=docket_status,
                progress_percent=docket_progress
            ),
            search_opinioncluster=TableImportProgress(
                table_name="search_opinioncluster",
                current_count=cluster_count,
                expected_count=EXPECTED_COUNTS["search_opinioncluster"],
                status=cluster_status,
                progress_percent=cluster_progress
            ),
            search_opinionscited=TableImportProgress(
                table_name="search_opinionscited",
                current_count=citation_count,
                expected_count=EXPECTED_COUNTS["search_opinionscited"],
                status=citation_status,
                progress_percent=citation_progress
            ),
            search_parenthetical=TableImportProgress(
                table_name="search_parenthetical",
                current_count=parenthetical_count,
                expected_count=EXPECTED_COUNTS["search_parenthetical"],
                status=parenthetical_status,
                progress_percent=parenthetical_progress
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting import progress: {str(e)}")


@router.post("/import", response_model=ImportStatus)
async def start_import(request: ImportRequest):
    """
    Start importing data from downloaded CSV files.
    
    This endpoint queues a Celery task for background import processing.
    
    Args:
        request: Import request with date and optional table list
    """
    try:
        # Verify files exist
        files_exist = importer.verify_files_exist(request.date, request.tables)
        missing_files = [t for t, exists in files_exist.items() if not exists]
        
        # Check if we have at least some files to import
        available_files = [t for t, exists in files_exist.items() if exists]
        if not available_files:
            raise HTTPException(
                status_code=400,
                detail=f"No CSV files found for date {request.date}. Please download the dataset first. Note: CSV files may not be available for this date in S3."
            )
        
        # Warn about missing files but allow import to proceed with available files
        if missing_files:
            logger.warning(f"Some CSV files are missing for date {request.date}: {missing_files}. Import will proceed with available files only.")
        
        # Queue Celery task
        task = import_dataset_task.delay(
            date=request.date,
            tables=request.tables
        )
        
        # Store task ID for status tracking
        import_tasks[request.date] = task.id
        
        # Get total number of tables to import
        tables_to_import = request.tables or importer.IMPORT_ORDER
        tables_total = len([t for t in tables_to_import if t in importer.IMPORT_ORDER])
        
        return ImportStatus(
            status="pending",
            date=request.date,
            tables_total=tables_total,
            progress=0.0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-caselaw-sync")
def import_caselaw_sync():
    """
    SYNCHRONOUS import of caselaw tables - no threading.
    Uses existing downloaded files if present on volume.

    Run this AFTER import-people-db-sync completes.
    """
    from pathlib import Path
    from app.core.database import SessionLocal

    try:
        date = "2025-10-31"
        logger.info("=" * 80)
        logger.info("SYNCHRONOUS CASELAW IMPORT STARTED")
        logger.info("=" * 80)

        tables = [
            ("search_docket", f"dockets-{date}.csv.bz2"),
            ("search_opinioncluster", f"opinion-clusters-{date}.csv.bz2"),
            ("search_opinionscited", f"opinions-cited-{date}.csv.bz2"),
            ("search_parenthetical", f"parentheticals-{date}.csv.bz2"),
        ]

        session = SessionLocal()
        results = []

        for table_name, s3_file in tables:
            try:
                from app.core.config import settings
                data_dir = Path(settings.DATA_DIR)
                data_dir.mkdir(parents=True, exist_ok=True)

                target_path = data_dir / f"{table_name}-{date}.csv"

                # Check if file exists
                if not target_path.exists():
                    logger.info(f"[{table_name}] Downloading from S3: {s3_file}")
                    downloaded_path = downloader.download_file(
                        key=f"bulk-data/{s3_file}",
                        target_path=target_path
                    )
                    logger.info(f"[{table_name}] Download complete: {downloaded_path.stat().st_size / (1024**3):.2f} GB")
                else:
                    logger.info(f"[{table_name}] Using existing file: {target_path}")
                    logger.info(f"[{table_name}] File size: {target_path.stat().st_size / (1024**3):.2f} GB")
                    downloaded_path = target_path

                # Import
                logger.info(f"[{table_name}] Starting import to database")
                row_count = importer.import_csv(table_name, downloaded_path, session)

                logger.info(f"[{table_name}] ✓ Import complete: {row_count:,} rows")
                results.append({
                    "table": table_name,
                    "status": "success",
                    "rows": row_count
                })

            except Exception as e:
                logger.error(f"[{table_name}] Error: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    "table": table_name,
                    "status": "error",
                    "error": str(e)
                })

        session.close()

        logger.info("=" * 80)
        logger.info("CASELAW IMPORT COMPLETE")
        logger.info("=" * 80)

        return {
            "status": "completed",
            "message": "Caselaw import completed",
            "date": date,
            "results": results
        }

    except Exception as e:
        logger.error(f"Fatal error in caselaw import: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-parallel")
async def start_parallel_import():
    """
    Start parallel import directly from S3 to Railway database.

    This downloads all 4 tables from S3 and imports them in parallel.
    Much faster than sequential import or dump/restore.
    """
    try:
        import threading

        # Use latest date
        date = "2025-10-31"

        # Start import in a daemon thread so it persists after response
        thread = threading.Thread(
            target=run_parallel_import_sync,
            args=(date,),
            daemon=False  # Keep thread alive even after response
        )
        thread.start()

        return {
            "status": "started",
            "message": f"Parallel import from S3 started for date {date}",
            "date": date,
            "tables": ["search_docket", "search_opinioncluster", "search_opinionscited", "search_parenthetical"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_parallel_import_sync(date: str):
    """
    Synchronous wrapper to run async parallel import in a thread.
    """
    import asyncio
    asyncio.run(parallel_import_from_s3(date))


async def parallel_import_from_s3(date: str):
    """
    Background task to download and import all tables in parallel from S3.
    """
    import asyncio
    from pathlib import Path
    from app.core.database import SessionLocal

    logger.info(f"Starting parallel import from S3 for date {date}")

    # Table mappings: (table_name, s3_file_name)
    tables = [
        ("search_docket", f"dockets-{date}.csv.bz2"),
        ("search_opinioncluster", f"opinion-clusters-{date}.csv.bz2"),
        ("search_opinionscited", f"opinions-cited-{date}.csv.bz2"),
        ("search_parenthetical", f"parentheticals-{date}.csv.bz2"),
    ]

    async def download_and_import_table(table_name: str, s3_file: str):
        """Download and import a single table."""
        try:
            logger.info(f"[{table_name}] Starting download from S3: {s3_file}")

            # Download from S3 to Railway volume
            from app.core.config import settings
            data_dir = Path(settings.DATA_DIR)
            data_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

            target_path = data_dir / f"{table_name}-{date}.csv"
            downloaded_path = downloader.download_file(
                key=f"bulk-data/{s3_file}",
                target_path=target_path
            )

            logger.info(f"[{table_name}] Download complete: {downloaded_path}")
            logger.info(f"[{table_name}] File size: {downloaded_path.stat().st_size / (1024**3):.2f} GB")

            # Import to database
            logger.info(f"[{table_name}] Starting import to database")
            session = SessionLocal()
            try:
                row_count = importer.import_csv(table_name, downloaded_path, session)
                logger.info(f"[{table_name}] ✓ Import complete: {row_count:,} rows")
                return {
                    "table": table_name,
                    "status": "success",
                    "rows": row_count
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"[{table_name}] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "table": table_name,
                "status": "error",
                "error": str(e)
            }

    # Run all imports in parallel
    tasks = [
        download_and_import_table(table_name, s3_file)
        for table_name, s3_file in tables
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("=" * 80)
    logger.info("PARALLEL IMPORT COMPLETE")
    logger.info("=" * 80)
    for result in results:
        if isinstance(result, dict):
            logger.info(f"{result['table']}: {result['status']}")
        else:
            logger.error(f"Unexpected result: {result}")

    return results


@router.post("/import-people-db-sync")
def import_people_database_sync():
    """
    SYNCHRONOUS import of people database tables - no threading.
    This blocks until complete but provides full logging visibility.

    Run this BEFORE importing caselaw tables.
    """
    from pathlib import Path
    from app.core.database import SessionLocal

    try:
        date = "2025-10-31"
        logger.info("=" * 80)
        logger.info("SYNCHRONOUS PEOPLE DATABASE IMPORT STARTED")
        logger.info("=" * 80)

        tables = [
            ("people_db_court", f"courts-{date}.csv.bz2"),
            ("people_db_person", f"people-db-people-{date}.csv.bz2"),
        ]

        session = SessionLocal()
        results = []

        for table_name, s3_file in tables:
            try:
                logger.info(f"\n[{table_name}] Starting download from S3: {s3_file}")

                from app.core.config import settings
                data_dir = Path(settings.DATA_DIR)
                data_dir.mkdir(parents=True, exist_ok=True)

                target_path = data_dir / f"{table_name}-{date}.csv"

                # Download
                downloaded_path = downloader.download_file(
                    key=f"bulk-data/{s3_file}",
                    target_path=target_path
                )

                logger.info(f"[{table_name}] Download complete: {downloaded_path}")
                logger.info(f"[{table_name}] File size: {downloaded_path.stat().st_size / (1024**2):.2f} MB")

                # Import
                logger.info(f"[{table_name}] Starting import to database")

                # Use pandas for both tables to handle CSV format issues
                if table_name == "people_db_person":
                    logger.info(f"[{table_name}] Using pandas import with self-referential FK handling")
                    row_count = importer.import_csv_pandas(
                        table_name,
                        downloaded_path,
                        session,
                        skip_self_referential_fk=True
                    )
                elif table_name == "people_db_court":
                    logger.info(f"[{table_name}] Using pandas import with self-referential FK handling")
                    row_count = importer.import_csv_pandas(
                        table_name,
                        downloaded_path,
                        session,
                        skip_self_referential_fk=True
                    )
                else:
                    row_count = importer.import_csv(table_name, downloaded_path, session)

                logger.info(f"[{table_name}] ✓ Import complete: {row_count:,} rows")
                results.append({
                    "table": table_name,
                    "status": "success",
                    "rows": row_count
                })

            except Exception as e:
                logger.error(f"[{table_name}] Error: {e}")
                import traceback
                traceback.print_exc()
                results.append({
                    "table": table_name,
                    "status": "error",
                    "error": str(e)
                })

        session.close()

        logger.info("=" * 80)
        logger.info("PEOPLE DATABASE IMPORT COMPLETE")
        logger.info("=" * 80)

        return {
            "status": "completed",
            "message": "People database import completed",
            "date": date,
            "results": results
        }

    except Exception as e:
        logger.error(f"Fatal error in people DB import: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-people-db")
async def import_people_database():
    """
    Import people database tables (courts and people) before caselaw tables.

    These tables contain foreign key dependencies required by caselaw tables:
    - people_db_court: Required by search_docket.court_id
    - people_db_person: Required by search_docket.assigned_to_id, referred_to_id

    This should be run BEFORE import-parallel for caselaw tables.
    """
    try:
        import threading

        # Use latest date
        date = "2025-10-31"

        # Start import in a daemon thread
        thread = threading.Thread(
            target=run_people_db_import_sync,
            args=(date,),
            daemon=False
        )
        thread.start()

        return {
            "status": "started",
            "message": f"People database import started for date {date}",
            "date": date,
            "tables": ["people_db_court", "people_db_person"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def run_people_db_import_sync(date: str):
    """Synchronous wrapper to run async people DB import in a thread."""
    import asyncio
    asyncio.run(import_people_database_tables(date))


async def import_people_database_tables(date: str):
    """
    Background task to download and import people database tables.
    These tables MUST be imported before caselaw tables due to foreign key constraints.
    """
    import asyncio
    from pathlib import Path
    from app.core.database import SessionLocal

    logger.info(f"Starting people database import from S3 for date {date}")

    # Table mappings: (table_name, s3_file_name)
    tables = [
        ("people_db_court", f"courts-{date}.csv.bz2"),
        ("people_db_person", f"people-db-people-{date}.csv.bz2"),
    ]

    async def download_and_import_table(table_name: str, s3_file: str):
        """Download and import a single table."""
        try:
            logger.info(f"[{table_name}] Starting download from S3: {s3_file}")

            # Download from S3 to Railway volume
            from app.core.config import settings
            data_dir = Path(settings.DATA_DIR)
            data_dir.mkdir(parents=True, exist_ok=True)

            target_path = data_dir / f"{table_name}-{date}.csv"
            downloaded_path = downloader.download_file(
                key=f"bulk-data/{s3_file}",
                target_path=target_path
            )

            logger.info(f"[{table_name}] Download complete: {downloaded_path}")
            logger.info(f"[{table_name}] File size: {downloaded_path.stat().st_size / (1024**3):.2f} GB")

            # Import to database
            logger.info(f"[{table_name}] Starting import to database")
            session = SessionLocal()
            try:
                # Use pandas import with self-referential FK skip for people_db_person
                if table_name == "people_db_person":
                    logger.info(f"[{table_name}] Using pandas import with self-referential FK handling")
                    row_count = importer.import_csv_pandas(
                        table_name,
                        downloaded_path,
                        session,
                        skip_self_referential_fk=True
                    )
                else:
                    row_count = importer.import_csv(table_name, downloaded_path, session)

                logger.info(f"[{table_name}] ✓ Import complete: {row_count:,} rows")
                return {
                    "table": table_name,
                    "status": "success",
                    "rows": row_count
                }
            finally:
                session.close()

        except Exception as e:
            logger.error(f"[{table_name}] Error: {e}")
            import traceback
            traceback.print_exc()
            return {
                "table": table_name,
                "status": "error",
                "error": str(e)
            }

    # Run all imports in parallel
    tasks = [
        download_and_import_table(table_name, s3_file)
        for table_name, s3_file in tables
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("=" * 80)
    logger.info("PEOPLE DATABASE IMPORT COMPLETE")
    logger.info("=" * 80)
    for result in results:
        if isinstance(result, dict):
            logger.info(f"{result['table']}: {result['status']}")
        else:
            logger.error(f"Unexpected result: {result}")

    return results


@router.get("/import/status/{date}", response_model=ImportStatus)
async def get_import_status(date: str, db: Session = Depends(get_db)):
    """
    Get the status of an import operation.

    Checks Celery task status if a task exists, otherwise checks database.

    Args:
        date: Date string (YYYY-MM-DD)
        db: Database session
    """
    # Check if there's an active task
    task_id = import_tasks.get(date)

    if task_id:
        task = AsyncResult(task_id, app=celery_app)

        try:
            task_state = task.state
        except (ValueError, KeyError) as e:
            # Handle Celery serialization errors
            print(f"Error getting task state: {e}")
            # Clean up the bad task reference
            import_tasks.pop(date, None)
            # Continue to check database status below
            task_id = None

        if task_id:  # Only proceed if task state was accessible
            error = None  # Initialize error
            if task_state == 'PENDING':
                status = "pending"
                progress = 0.0
                current_table = None
                tables_completed = []
                records_imported = {}
            elif task_state == 'PROGRESS':
                status = "importing"
                meta = task.info or {}
                progress = meta.get('progress', 0.0)
                current_table = meta.get('current_table')
                tables_completed = meta.get('tables_completed', [])
                records_imported = meta.get('records_imported', {})
            elif task_state == 'SUCCESS':
                status = "completed"
                result = task.result or {}
                progress = 1.0
                current_table = None
                tables_completed = result.get('tables_completed', [])
                records_imported = result.get('records_imported', {})
                # Remove completed task from tracking
                import_tasks.pop(date, None)
            else:  # FAILURE
                status = "failed"
                try:
                    meta = task.info if isinstance(task.info, dict) else {}
                    error = meta.get('error', str(task.info)) if meta else str(task.info)
                except Exception:
                    error = 'Import task failed'
                progress = 0.0
                current_table = None
                tables_completed = []
                records_imported = {}
                # Remove failed task from tracking
                import_tasks.pop(date, None)

            return ImportStatus(
                status=status,
                date=date,
                current_table=current_table,
                tables_completed=tables_completed,
                tables_total=len(tables_completed) + (1 if current_table else 0),
                progress=progress,
                records_imported=records_imported,
                error=error
            )
    
    # No active task - check if data exists in database
    try:
        total_people = db.query(func.count(Person.id)).scalar() or 0
        
        if total_people > 0:
            # Data exists, assume import was completed
            return ImportStatus(
                status="completed",
                date=date,
                tables_completed=list(importer.IMPORT_ORDER),
                tables_total=len(importer.IMPORT_ORDER),
                progress=1.0
            )
        else:
            return ImportStatus(
                status="pending",
                date=date,
                tables_total=len(importer.IMPORT_ORDER),
                progress=0.0
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking import status: {str(e)}")


@router.post("/import-caselaw-background")
def import_caselaw_background():
    """
    Start caselaw import as a detached background process using nohup.
    This endpoint returns immediately and the import runs independently.

    Monitor progress via /api/monitoring/import/live-status
    """
    import subprocess
    from pathlib import Path

    try:
        # Path to the import script
        script_path = "/app/import_directly.py"
        log_path = "/app/data/import.log"

        # Verify script exists
        if not Path(script_path).exists():
            raise FileNotFoundError(f"Import script not found: {script_path}")

        # Use nohup and shell redirect to truly background the process
        # This ensures the process survives after the HTTP request completes
        cmd = f"nohup python3 {script_path} > {log_path} 2>&1 &"

        # Execute via shell to get proper backgrounding
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )

        logger.info(f"Started caselaw import with nohup (command: {cmd})")
        logger.info(f"Logs will be written to: {log_path}")

        return {
            "status": "started",
            "message": "Caselaw import started in background with nohup",
            "log_file": log_path,
            "note": "Monitor progress at /api/monitoring/import/live-status or GET /api/data/import-logs"
        }
    except Exception as e:
        logger.error(f"Failed to start background import: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start import: {str(e)}")


@router.get("/import-logs")
def get_import_logs(lines: int = 100):
    """
    Get the last N lines from the import log file.

    Args:
        lines: Number of lines to return (default 100, max 1000)
    """
    from pathlib import Path

    try:
        log_path = Path("/app/data/import.log")

        if not log_path.exists():
            return {
                "status": "no_log",
                "message": "Import log file does not exist yet. Import may not have started.",
                "log_path": str(log_path)
            }

        # Limit lines to prevent huge responses
        lines = min(lines, 1000)

        # Read last N lines using tail command (more efficient than reading entire file)
        import subprocess
        result = subprocess.run(
            ["tail", f"-{lines}", str(log_path)],
            capture_output=True,
            text=True
        )

        return {
            "status": "success",
            "lines": lines,
            "log_path": str(log_path),
            "log_content": result.stdout
        }
    except Exception as e:
        logger.error(f"Failed to read import logs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read logs: {str(e)}")
