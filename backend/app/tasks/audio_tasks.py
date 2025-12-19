"""
Synchronous tasks for audio generation using TTS.
Handles chapter-to-audio conversion with automatic chunking and file management.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import asyncio
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.chapter import Chapter
from app.models.audio_file import AudioFile
from app.models.processing_job import ProcessingJob, JobType, JobStatus
from app.services.tts_service import get_tts_service, TTSConfig
from app.config import settings

logger = logging.getLogger(__name__)


def get_audio_storage_path(book_id: str, chapter_id: str) -> Path:
    """
    Get the storage path for audio files.

    Args:
        book_id: Book UUID
        chapter_id: Chapter UUID

    Returns:
        Path to audio directory for this chapter
    """
    audio_dir = Path(settings.AUDIO_STORAGE_PATH) / str(book_id) / str(chapter_id)
    audio_dir.mkdir(parents=True, exist_ok=True)
    return audio_dir


async def save_audio_chunk(
    audio_data: bytes,
    book_id: str,
    chapter_id: str,
    chunk_index: int,
    total_chunks: int,
    format: str = "wav",
) -> Path:
    """
    Save audio chunk to disk.

    Args:
        audio_data: Audio file bytes
        book_id: Book UUID
        chapter_id: Chapter UUID
        chunk_index: Index of this chunk
        total_chunks: Total number of chunks
        format: Audio format (default: wav)

    Returns:
        Path to saved file
    """
    audio_dir = get_audio_storage_path(book_id, chapter_id)

    if total_chunks == 1:
        filename = f"chapter_{chapter_id}.{format}"
    else:
        filename = f"chapter_{chapter_id}_chunk_{chunk_index:03d}.{format}"

    file_path = audio_dir / filename

    with open(file_path, "wb") as f:
        f.write(audio_data)

    logger.info(f"Saved audio chunk to {file_path} ({len(audio_data)} bytes)")
    return file_path


def update_job_progress(
    db: Session,
    job_id: str,
    progress_percent: int,
    metadata: Optional[dict] = None,
):
    """
    Update job progress in database.

    Args:
        db: Database session
        job_id: Job UUID
        progress_percent: Progress percentage (0-100)
        metadata: Optional metadata to update
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if job:
        job.progress_percent = progress_percent
        if metadata:
            job.job_metadata = {**(job.job_metadata or {}), **metadata}
        db.commit()


def generate_audio_sync(
    chapter_id: str,
    voice: Optional[str] = None,
    language: Optional[str] = None,
    exaggeration: float = 0.8,
    cfg_weight: float = 0.3,
    temperature: float = 0.9,
):
    """
    Generate audio from formatted chapter text using TTS (synchronous version).

    Args:
        chapter_id: Chapter UUID
        voice: Optional voice name from library
        language: Optional language code
        exaggeration: TTS exaggeration parameter
        cfg_weight: TTS CFG weight parameter
        temperature: TTS temperature parameter

    Workflow:
        1. Load chapter.formatted_text from database
        2. Chunk text according to TTS limits
        3. Generate audio for each chunk via Chatterbox API
        4. Save audio files to storage
        5. Create AudioFile records in database
        6. Update chapter.status = 'completed'
    """
    db = SessionLocal()
    job_id = None
    chapter = None

    try:
        # Load chapter
        chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
        if not chapter:
            raise ValueError(f"Chapter {chapter_id} not found")

        book_id = str(chapter.book_id)

        # Create processing job
        job = ProcessingJob(
            book_id=chapter.book_id,
            chapter_id=chapter.id,
            job_type=JobType.GENERATE_AUDIO,
            status=JobStatus.RUNNING,
            progress_percent=0,
            metadata={
                "voice": voice,
                "language": language,
                "exaggeration": exaggeration,
                "cfg_weight": cfg_weight,
                "temperature": temperature,
            },
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        job_id = str(job.id)

        # Update chapter status
        chapter.status = "processing"
        db.commit()

        logger.info(
            f"Starting audio generation for chapter {chapter_id} "
            f"(book {book_id}, job {job_id})"
        )

        # Verify formatted text exists
        if not chapter.formatted_text:
            raise ValueError(
                f"Chapter {chapter_id} has no formatted_text. "
                "Run format_chapter_sync first."
            )

        # Configure TTS
        tts_config = TTSConfig(
            voice=voice,
            language=language,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            temperature=temperature,
        )

        # Run async TTS generation
        async def generate():
            async with await get_tts_service() as tts_service:
                # Health check
                if not await tts_service.health_check():
                    raise RuntimeError("Chatterbox TTS service is not available")

                # Generate speech with automatic chunking
                results = await tts_service.generate_speech_from_chunks(
                    text=chapter.formatted_text,
                    config=tts_config,
                )

                total_chunks = len(results)
                logger.info(f"Generated {total_chunks} audio chunks")

                # Save chunks and create AudioFile records
                audio_files = []
                for i, result in enumerate(results):
                    # Update progress
                    progress = int((i + 1) / total_chunks * 90)  # 0-90%
                    update_job_progress(db, job_id, progress)

                    # Save audio file
                    file_path = await save_audio_chunk(
                        audio_data=result.audio_data,
                        book_id=book_id,
                        chapter_id=chapter_id,
                        chunk_index=result.chunk_index,
                        total_chunks=result.total_chunks,
                        format=result.format,
                    )

                    # Create AudioFile record
                    audio_file = AudioFile(
                        chapter_id=chapter.id,
                        file_path=str(file_path),
                        file_size=len(result.audio_data),
                        format=result.format,
                        chunk_index=result.chunk_index,
                        total_chunks=result.total_chunks,
                        tts_model="chatterbox-turbo",
                        voice_id=voice,
                        duration_seconds=result.duration_seconds,
                    )
                    db.add(audio_file)
                    audio_files.append(audio_file)

                db.commit()
                return audio_files

        # Execute async task
        audio_files = asyncio.run(generate())

        # Update chapter status
        chapter.status = "completed"
        db.commit()

        # Update job to completed
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = JobStatus.COMPLETED
        job.progress_percent = 100
        job.completed_at = datetime.utcnow()
        job.job_metadata = {
            **(job.job_metadata or {}),
            "audio_files_count": len(audio_files),
            "total_size_bytes": sum(af.file_size for af in audio_files),
        }
        db.commit()

        logger.info(
            f"Audio generation completed for chapter {chapter_id}: "
            f"{len(audio_files)} files created"
        )

        return {
            "chapter_id": chapter_id,
            "audio_files_count": len(audio_files),
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Audio generation failed for chapter {chapter_id}: {e}")

        # Update chapter status
        if chapter:
            chapter.status = "failed"
            chapter.error_message = str(e)
            db.commit()

        # Update job status
        if job_id:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()

        raise

    finally:
        db.close()


def generate_book_audio_sync(
    book_id: str,
    voice: Optional[str] = None,
    language: Optional[str] = None,
):
    """
    Generate audio for all chapters in a book (synchronous version).

    Args:
        book_id: Book UUID
        voice: Optional voice name
        language: Optional language code

    This function processes each chapter sequentially.
    """
    db = SessionLocal()

    try:
        # Get all formatted chapters for this book
        chapters = (
            db.query(Chapter)
            .filter(Chapter.book_id == book_id)
            .filter(Chapter.status == "formatted")
            .order_by(Chapter.chapter_number)
            .all()
        )

        if not chapters:
            raise ValueError(
                f"No formatted chapters found for book {book_id}. "
                "Run format_chapter_sync first."
            )

        logger.info(f"Generating audio for {len(chapters)} chapters in book {book_id}")

        # Process each chapter sequentially
        results = []
        for chapter in chapters:
            chapter_id = str(chapter.id)
            db.close()  # Close session before calling sync function

            result = generate_audio_sync(
                chapter_id=chapter_id,
                voice=voice,
                language=language,
            )
            results.append(result)

            db = SessionLocal()  # Reopen for next iteration

        return {
            "book_id": book_id,
            "chapters_count": len(chapters),
            "results": results,
            "status": "completed",
        }

    except Exception as e:
        logger.error(f"Failed to generate audio for book {book_id}: {e}")
        raise

    finally:
        db.close()
