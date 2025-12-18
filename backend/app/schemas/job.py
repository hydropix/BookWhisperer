from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.processing_job import JobType, JobStatus


class ProcessingJobBase(BaseModel):
    job_type: JobType


class ProcessingJobCreate(ProcessingJobBase):
    book_id: UUID
    chapter_id: Optional[UUID] = None
    celery_task_id: Optional[str] = None


class ProcessingJobRead(ProcessingJobBase):
    id: UUID
    book_id: UUID
    chapter_id: Optional[UUID] = None
    celery_task_id: Optional[str] = None
    status: JobStatus
    progress_percent: int
    error_message: Optional[str] = None
    retry_count: int
    max_retries: int
    metadata: Dict[str, Any] = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingJobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    progress_percent: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: Optional[int] = None
    celery_task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
