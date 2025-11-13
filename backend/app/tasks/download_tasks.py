"""
Download Tasks

Celery tasks for downloading files from S3 in the background.
"""
from celery import Task
from app.celery_app import celery_app
from app.services.s3_downloader import CourtListenerDownloader
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

downloader = CourtListenerDownloader()


@celery_app.task(bind=True, name="download_dataset")
def download_dataset_task(
    self: Task,
    date: str,
    tables: Optional[List[str]] = None
) -> dict:
    """
    Background task to download a dataset.
    
    Args:
        date: Date string (YYYY-MM-DD)
        tables: Optional list of table names to download
        
    Returns:
        Dictionary with download results
    """
    try:
        logger.info(f"Starting download for date {date}")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'downloading', 'date': date, 'progress': 0.0}
        )
        
        # Download files
        downloaded = downloader.download_dataset(date=date, tables=tables)
        
        # Build result
        result = {
            'status': 'completed',
            'date': date,
            'files': {name: str(path) for name, path in downloaded.items()},
            'progress': 1.0
        }
        
        logger.info(f"Download completed for date {date}")
        return result
        
    except Exception as e:
        logger.error(f"Download failed for date {date}: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'failed', 'error': str(e)}
        )
        raise


@celery_app.task(bind=True, name="download_file")
def download_file_task(
    self: Task,
    s3_key: str,
    target_filename: Optional[str] = None
) -> dict:
    """
    Background task to download a single file.
    
    Args:
        s3_key: S3 object key
        target_filename: Optional target filename
        
    Returns:
        Dictionary with download result
    """
    try:
        logger.info(f"Starting download for file {s3_key}")
        
        self.update_state(
            state='PROGRESS',
            meta={'status': 'downloading', 'progress': 0.0}
        )
        
        target_path = None
        if target_filename:
            from pathlib import Path
            from app.core.config import settings
            target_path = Path(settings.DATA_DIR) / target_filename
        
        downloaded_path = downloader.download_file(s3_key, target_path)
        
        result = {
            'status': 'completed',
            'file': str(downloaded_path),
            'size': downloaded_path.stat().st_size if downloaded_path.exists() else 0
        }
        
        logger.info(f"Download completed for file {s3_key}")
        return result
        
    except Exception as e:
        logger.error(f"Download failed for file {s3_key}: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'failed', 'error': str(e)}
        )
        raise

