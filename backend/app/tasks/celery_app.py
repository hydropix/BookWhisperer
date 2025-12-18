"""
Celery Application Configuration

Configures Celery for async task processing with Redis as broker.
"""

import logging
from celery import Celery
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize Celery app
celery_app = Celery(
    "bookwhisperer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit

    # Retry settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_persistent=True,

    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks

    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)

# Auto-discover tasks from tasks module
celery_app.autodiscover_tasks(['app.tasks'])

logger.info("Celery app initialized successfully")
