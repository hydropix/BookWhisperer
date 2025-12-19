"""
Chapter Processing Tasks - Synchronous tasks for chapter formatting using LLM.

This module contains:
- format_chapter_sync: Formats chapter text using Ollama LLM
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.chapter import Chapter
from app.models.processing_job import ProcessingJob, JobType, JobStatus
from app.services.llm_formatter import get_llm_formatter
from app.services.chunking import get_text_chunker

logger = logging.getLogger(__name__)


def format_chapter_sync(chapter_id: str, job_id: Optional[str] = None):
    """
    Format a chapter's text using Ollama LLM (synchronous version).

    This function:
    1. Loads the raw chapter text
    2. Chunks it if necessary for LLM context limits
    3. Formats each chunk using Ollama
    4. Reassembles and saves the formatted text
    5. Updates chapter status and job progress

    Args:
        chapter_id: UUID of the chapter to format
        job_id: Optional UUID of the processing job to track progress

    Raises:
        Exception: If formatting fails
    """
    db: Session = SessionLocal()
    job: Optional[ProcessingJob] = None

    try:
        logger.info(f"Starting format_chapter_sync for chapter_id={chapter_id}")

        # Load job if provided
        if job_id:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = JobStatus.RUNNING
                job.progress_percent = 0
                db.commit()

        # Load chapter
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            error_msg = f"Chapter not found: {chapter_id}"
            logger.error(error_msg)
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_msg
                db.commit()
            raise ValueError(error_msg)

        # Check if raw text exists
        if not chapter.raw_text or not chapter.raw_text.strip():
            error_msg = f"Chapter {chapter_id} has no raw text to format"
            logger.error(error_msg)
            chapter.status = "failed"
            chapter.error_message = error_msg
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_msg
            db.commit()
            raise ValueError(error_msg)

        # Update chapter status
        chapter.status = "formatting"
        chapter.error_message = None
        db.commit()

        # Get services
        chunker = get_text_chunker()
        formatter = get_llm_formatter()

        # Chunk the text for LLM processing
        logger.info(f"Chunking chapter text ({len(chapter.raw_text)} chars)")
        chunks = chunker.chunk_for_llm(
            text=chapter.raw_text,
            max_chars=3800,  # Leave some buffer below OLLAMA_MAX_TOKENS
            overlap_chars=200
        )
        logger.info(f"Created {len(chunks)} chunks")

        if job:
            job.job_metadata = job.job_metadata or {}
            job.job_metadata['total_chunks'] = len(chunks)
            db.commit()

        # Format each chunk
        formatted_chunks = []
        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Formatting chunk {i}/{len(chunks)} for chapter {chapter_id}")

            # Format the chunk
            formatted_chunk = formatter.format_text(chunk)
            formatted_chunks.append(formatted_chunk)

            # Update progress
            progress = int((i / len(chunks)) * 100)
            if job:
                job.progress_percent = progress
                job.job_metadata['current_chunk'] = i
                db.commit()

            logger.info(f"Progress: {progress}% ({i}/{len(chunks)} chunks)")

        # Reassemble formatted chunks
        logger.info(f"Reassembling {len(formatted_chunks)} formatted chunks")
        formatted_text = chunker.reassemble_chunks(
            formatted_chunks,
            remove_overlap=True
        )

        # Save formatted text
        chapter.formatted_text = formatted_text
        chapter.character_count = len(formatted_text)
        chapter.status = "formatted"
        db.commit()

        # Update job status
        if job:
            job.status = JobStatus.COMPLETED
            job.progress_percent = 100
            db.commit()

        logger.info(
            f"Successfully formatted chapter {chapter_id}: "
            f"{len(chapter.raw_text)} -> {len(formatted_text)} chars"
        )

        return {
            'chapter_id': str(chapter_id),
            'status': 'formatted',
            'chunks_processed': len(chunks),
            'original_length': len(chapter.raw_text),
            'formatted_length': len(formatted_text)
        }

    except Exception as e:
        error_msg = f"Error formatting chapter {chapter_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Update chapter status
        try:
            chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
            if chapter:
                chapter.status = "failed"
                chapter.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update chapter status: {db_error}")

        # Update job status
        if job:
            try:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                db.commit()
            except Exception as job_error:
                logger.error(f"Failed to update job status: {job_error}")

        raise

    finally:
        db.close()


def format_all_chapters_sync(book_id: str):
    """
    Format all chapters for a book (synchronous version).

    This function formats each chapter sequentially.

    Args:
        book_id: UUID of the book whose chapters should be formatted

    Returns:
        Dict with chapter IDs and their results
    """
    db: Session = SessionLocal()

    try:
        logger.info(f"Starting format_all_chapters_sync for book_id={book_id}")

        # Get all chapters for the book that are extracted but not formatted
        chapters = db.query(Chapter).filter(
            Chapter.book_id == book_id,
            Chapter.status == "extracted"
        ).all()

        if not chapters:
            logger.warning(f"No extracted chapters found for book {book_id}")
            return {
                'book_id': str(book_id),
                'chapters_formatted': 0,
                'message': 'No chapters to format'
            }

        # Format each chapter sequentially
        results = {}
        for chapter in chapters:
            # Create job record
            job = ProcessingJob(
                book_id=book_id,
                chapter_id=chapter.id,
                job_type=JobType.FORMAT_CHAPTER,
                status=JobStatus.PENDING,
                retry_count=0,
                max_retries=3
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            logger.info(f"Formatting chapter {chapter.id} (job_id={job.id})")

            # Close db session before calling sync function (it creates its own)
            db.close()

            # Format the chapter
            result = format_chapter_sync(str(chapter.id), str(job.id))
            results[str(chapter.id)] = result

            # Reopen session for next iteration
            db = SessionLocal()

        logger.info(f"Formatted {len(results)} chapters for book {book_id}")

        return {
            'book_id': str(book_id),
            'chapters_formatted': len(results),
            'results': results
        }

    except Exception as e:
        logger.error(
            f"Error in format_all_chapters_sync for book {book_id}: {str(e)}",
            exc_info=True
        )
        raise

    finally:
        db.close()
