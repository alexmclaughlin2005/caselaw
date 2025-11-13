"""
Import Tasks

Celery tasks for importing CSV data into PostgreSQL in the background.
"""
from celery import Task
from app.celery_app import celery_app
from app.services.data_importer import DataImporter
from app.services.data_validator import DataValidator
from app.core.database import SessionLocal
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

importer = DataImporter()
validator = DataValidator()


@celery_app.task(bind=True, name="import_dataset")
def import_dataset_task(
    self: Task,
    date: str,
    tables: Optional[List[str]] = None
) -> dict:
    """
    Background task to import a dataset.
    
    Args:
        date: Date string (YYYY-MM-DD)
        tables: Optional list of table names to import
        
    Returns:
        Dictionary with import results
    """
    session = SessionLocal()
    try:
        logger.info(f"Starting import for date {date}")
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'importing',
                'date': date,
                'progress': 0.0,
                'current_table': None,
                'tables_completed': []
            }
        )
        
        # Verify files exist and filter to only available files
        files_exist = importer.verify_files_exist(date, tables)
        available_tables = [t for t, exists in files_exist.items() if exists]
        missing_files = [t for t, exists in files_exist.items() if not exists]
        
        if not available_tables:
            raise ValueError(f"No CSV files found for date {date}. Please download the dataset first.")
        
        if missing_files:
            logger.warning(f"Some CSV files are missing for date {date}: {missing_files}. Import will proceed with available files only.")
        
        # Use only available tables for import
        tables = available_tables
        
        # Import dataset
        results = importer.import_dataset(date=date, tables=tables, db_session=session)
        
        # Update progress
        total_tables = len(results)
        completed = sum(1 for count in results.values() if count > 0)
        
        self.update_state(
            state='PROGRESS',
            meta={
                'status': 'validating',
                'date': date,
                'progress': 0.9,
                'tables_completed': list(results.keys()),
                'records_imported': results
            }
        )
        
        # Run validation
        validation_results = validator.run_full_validation(session)
        
        # Build result
        result = {
            'status': 'completed',
            'date': date,
            'records_imported': results,
            'validation': validation_results,
            'tables_total': total_tables,
            'tables_completed': completed
        }
        
        logger.info(f"Import completed for date {date}")
        return result
        
    except Exception as e:
        logger.error(f"Import failed for date {date}: {str(e)}")
        self.update_state(
            state='FAILURE',
            meta={'status': 'failed', 'error': str(e)}
        )
        raise
    finally:
        session.close()

