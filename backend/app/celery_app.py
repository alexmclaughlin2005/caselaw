"""
Celery Application Configuration

Sets up Celery for background task processing (downloads, imports).
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "courtlistener",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Import tasks so they're registered with Celery
from app.tasks import download_tasks, import_tasks

