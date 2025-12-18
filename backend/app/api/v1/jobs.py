"""
Processing Jobs API Endpoints

Handles job status tracking and monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.processing_job import ProcessingJob
from app.schemas.job import JobRead, JobList

router = APIRouter()


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific job by ID

    Args:
        job_id: Job UUID
        db: Database session

    Returns:
        JobRead: Job details
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    return job


@router.get("/books/{book_id}/jobs", response_model=JobList)
async def list_book_jobs(
    book_id: str,
    db: Session = Depends(get_db)
):
    """
    List all jobs for a book

    Args:
        book_id: Book UUID
        db: Database session

    Returns:
        JobList: List of jobs
    """
    jobs = db.query(ProcessingJob).filter(
        ProcessingJob.book_id == book_id
    ).order_by(ProcessingJob.created_at.desc()).all()

    return JobList(
        jobs=jobs,
        total=len(jobs)
    )


@router.get("/celery/{celery_task_id}", response_model=JobRead)
async def get_job_by_celery_id(
    celery_task_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a job by Celery task ID

    Args:
        celery_task_id: Celery task ID
        db: Database session

    Returns:
        JobRead: Job details
    """
    job = db.query(ProcessingJob).filter(
        ProcessingJob.celery_task_id == celery_task_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with celery_task_id {celery_task_id} not found"
        )

    return job
