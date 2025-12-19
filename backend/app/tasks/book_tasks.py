"""
Book Processing Tasks

Synchronous tasks for parsing books and extracting chapters.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.processing_job import ProcessingJob, JobType, JobStatus
from app.services.epub_parser import parse_epub
from app.services.txt_parser import parse_txt

logger = logging.getLogger(__name__)


def parse_book_sync(book_id: str):
    """
    Parse a book file and extract chapters (synchronous version).

    This function:
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
        logger.info(f"Starting parse_book_sync for book_id: {book_id}")

        # Get book from database
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise ValueError(f"Book not found: {book_id}")

        # Create processing job record
        job = ProcessingJob(
            book_id=book_id,
            job_type=JobType.PARSE_BOOK,
            status=JobStatus.RUNNING,
            progress_percent=0,
            started_at=datetime.utcnow()
        )
        db.add(job)
        db.commit()

        # Update book status
        book.status = "parsing"
        db.commit()

        logger.info(f"Processing {book.file_type.value.upper()} file: {book.file_path}")

        # Parse based on file type
        if book.file_type.value == "epub":
            result = parse_epub(book.file_path)
        elif book.file_type.value == "txt":
            result = parse_txt(book.file_path)
        else:
            raise ValueError(f"Unsupported file type: {book.file_type.value}")

        # Update progress
        job.progress_percent = 50
        db.commit()

        # Update book metadata
        metadata = result.get("metadata", {})
        if metadata:
            book.title = metadata.get("title", book.title)
            book.author = metadata.get("author", book.author)
            book.book_metadata = metadata

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

        raise

    finally:
        db.close()
