"""
Book Processing Tasks

Celery tasks for parsing books and extracting chapters.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.processing_job import ProcessingJob, JobType, JobStatus
from app.services.epub_parser import parse_epub
from app.services.txt_parser import parse_txt

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="tasks.parse_book")
def parse_book_task(self, book_id: str):
    """
    Parse a book file and extract chapters.

    This task:
    1. Loads the book from the database
    2. Determines the file type (EPUB or TXT)
    3. Parses the file using the appropriate parser
    4. Creates chapter records in the database
    5. Updates the book status

    Args:
        book_id: UUID of the book to parse

    Returns:
        Dict with parsing results
    """
    db = SessionLocal()
    job = None

    try:
        logger.info(f"Starting parse_book task for book_id: {book_id}")

        # Get book from database
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError(f"Book not found: {book_id}")

        # Create processing job record
        job = ProcessingJob(
            book_id=book_id,
            job_type=JobType.PARSE_BOOK,
            celery_task_id=self.request.id,
            status=JobStatus.RUNNING,
            progress_percent=0,
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        # Update book status
        book.status = "parsing"
        db.commit()

        logger.info(f"Processing {book.file_type.upper()} file: {book.file_path}")

        # Parse based on file type
        if book.file_type == "epub":
            result = parse_epub(book.file_path)
        elif book.file_type == "txt":
            result = parse_txt(book.file_path)
        else:
            raise ValueError(f"Unsupported file type: {book.file_type}")

        # Update progress
        job.progress_percent = 50
        db.commit()

        # Update book metadata
        metadata = result.get("metadata", {})
        if metadata:
            book.title = metadata.get("title", book.title)
            book.author = metadata.get("author", book.author)
            book.metadata = metadata

        # Create chapter records
        chapters_data = result.get("chapters", [])
        logger.info(f"Creating {len(chapters_data)} chapter records")

        for chapter_data in chapters_data:
            chapter = Chapter(
                book_id=book_id,
                chapter_number=chapter_data.chapter_number,
                title=chapter_data.title,
                raw_text=chapter_data.content,
                word_count=chapter_data.word_count,
                character_count=chapter_data.character_count,
                status="extracted"
            )
            db.add(chapter)

        # Update book
        book.total_chapters = len(chapters_data)
        book.status = "parsed"

        # Update job
        job.status = JobStatus.COMPLETED
        job.progress_percent = 100
        job.completed_at = datetime.utcnow()

        db.commit()

        logger.info(f"Successfully parsed book {book_id}: {len(chapters_data)} chapters")

        return {
            "book_id": book_id,
            "total_chapters": len(chapters_data),
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error parsing book {book_id}: {str(e)}", exc_info=True)

        # Update book status
        if db.query(Book).filter(Book.id == book_id).first():
            book = db.query(Book).filter(Book.id == book_id).first()
            book.status = "error"
            book.error_message = str(e)

        # Update job status
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

        db.commit()

        # Re-raise for Celery retry mechanism
        raise

    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.retry_parse_book", max_retries=3)
def retry_parse_book_task(self, book_id: str):
    """
    Wrapper task for parse_book with retry logic.

    Args:
        book_id: UUID of the book to parse
    """
    try:
        return parse_book_task(book_id)
    except Exception as e:
        logger.warning(f"Parse book failed, attempt {self.request.retries + 1}/3: {e}")

        # Exponential backoff: 2^retry_count seconds
        countdown = 2 ** self.request.retries

        # Update retry count in database
        db = SessionLocal()
        try:
            job = db.query(ProcessingJob).filter(
                ProcessingJob.celery_task_id == self.request.id
            ).first()

            if job:
                job.retry_count = self.request.retries + 1
                db.commit()
        finally:
            db.close()

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=countdown)
