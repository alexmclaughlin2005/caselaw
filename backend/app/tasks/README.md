# Tasks - Documentation

## Purpose
The `tasks` directory contains Celery background tasks for long-running operations like downloads and imports.

## Task Modules

### `download_tasks.py`
**Purpose**: Background tasks for downloading files from S3.

**Tasks**:
- `download_dataset_task`: Downloads an entire dataset (schema + CSV files)
- `download_file_task`: Downloads a single file

**Usage**:
```python
from app.tasks.download_tasks import download_dataset_task

# Queue a download task
task = download_dataset_task.delay(date="2024-10-31", tables=None)

# Check task status
result = task.get()  # Blocks until complete
# Or check status asynchronously
status = task.status
```

**Task States**:
- `PENDING`: Task is waiting to be processed
- `PROGRESS`: Task is currently running
- `SUCCESS`: Task completed successfully
- `FAILURE`: Task failed with an error

**Progress Tracking**:
Tasks update their state with progress information:
```python
self.update_state(
    state='PROGRESS',
    meta={'status': 'downloading', 'progress': 0.5}
)
```

## Dependencies
- **Depends on**: 
  - `app.celery_app` for Celery configuration
  - `app.services.s3_downloader` for download functionality
- **Used by**: 
  - API routes (via task.delay())
  - Celery workers (for execution)

## Integration
- Tasks are queued from API routes
- Celery workers process tasks in the background
- Task status can be checked via API endpoints
- Results are stored in Redis (Celery backend)

## Configuration
Celery is configured in `app/celery_app.py`:
- Broker: Redis
- Backend: Redis
- Serialization: JSON
- Time limits: 30 minutes hard, 25 minutes soft

## Running Celery Worker
```bash
# In Docker (already configured in docker-compose.yml)
docker-compose exec celery-worker celery -A app.celery_app worker --loglevel=info

# Locally
celery -A app.celery_app worker --loglevel=info
```

## Reference
See [AI_INSTRUCTIONS.md](../../AI_INSTRUCTIONS.md) for complete application overview.

