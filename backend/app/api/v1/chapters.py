from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.chapter import Chapter
from app.models.processing_job import ProcessingJob, JobType, JobStatus
from app.schemas.chapter import ChapterRead, ChapterList, ChapterUpdate
from app.schemas.job import JobRead
from app.tasks.chapter_tasks import format_chapter_sync, format_all_chapters_sync
from app.tasks.audio_tasks import generate_audio_sync, generate_book_audio_sync

router = APIRouter()


@router.get("/books/{book_id}/chapters", response_model=ChapterList)
async def list_chapters(book_id: str, db: Session = Depends(get_db)):
    """
    List all chapters for a book

    Args:
        book_id: Book UUID
        db: Database session

    Returns:
        ChapterList: List of chapters
    """
    chapters = db.query(Chapter).filter(
        Chapter.book_id == book_id
    ).order_by(Chapter.chapter_number).all()

    return ChapterList(
        chapters=chapters,
        total=len(chapters)
    )


@router.get("/chapters/{chapter_id}", response_model=ChapterRead)
async def get_chapter(chapter_id: str, db: Session = Depends(get_db)):
    """
    Get a specific chapter by ID

    Args:
        chapter_id: Chapter UUID
        db: Database session

    Returns:
        ChapterRead: Chapter details
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with id {chapter_id} not found"
        )
    return chapter


@router.patch("/chapters/{chapter_id}/exclude", response_model=ChapterRead)
async def toggle_chapter_exclude(chapter_id: str, db: Session = Depends(get_db)):
    """
    Toggle the excluded status of a chapter.

    Excluded chapters are skipped during batch processing (format all, generate all audio).

    Args:
        chapter_id: Chapter UUID
        db: Database session

    Returns:
        ChapterRead: Updated chapter details
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with id {chapter_id} not found"
        )

    chapter.excluded = not chapter.excluded
    db.commit()
    db.refresh(chapter)

    return chapter


@router.post("/chapters/{chapter_id}/format", response_model=JobRead)
async def format_chapter(chapter_id: str, db: Session = Depends(get_db)):
    """
    Start formatting a chapter using LLM.

    This endpoint:
    1. Validates the chapter exists and has raw text
    2. Creates a processing job
    3. Spawns a Celery task to format the chapter
    4. Returns the job details for tracking

    Args:
        chapter_id: Chapter UUID
        db: Database session

    Returns:
        JobRead: Processing job details

    Raises:
        404: Chapter not found
        400: Chapter has no raw text or is already being processed
    """
    # Check chapter exists
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with id {chapter_id} not found"
        )

    # Validate chapter has raw text
    if not chapter.raw_text or not chapter.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapter has no raw text to format"
        )

    # Check if already being processed
    if chapter.status == "formatting":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapter is already being formatted"
        )

    # Create processing job
    job = ProcessingJob(
        book_id=chapter.book_id,
        chapter_id=chapter.id,
        job_type=JobType.FORMAT_CHAPTER,
        status=JobStatus.PENDING,
        retry_count=0,
        max_retries=3
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run formatting synchronously
    format_chapter_sync(str(chapter.id), str(job.id))

    db.refresh(job)

    return job


@router.post("/books/{book_id}/chapters/format", response_model=dict)
async def format_all_chapters(book_id: str, db: Session = Depends(get_db)):
    """
    Start formatting all parsed chapters for a book.

    This endpoint spawns format tasks for all chapters that are in 'parsed' status.

    Args:
        book_id: Book UUID
        db: Database session

    Returns:
        dict: Summary of spawned tasks

    Raises:
        404: Book not found
        400: No chapters to format
    """
    # Check book exists
    from app.models.book import Book
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Check for extracted chapters
    chapters_count = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.status == "extracted"
    ).count()

    if chapters_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No extracted chapters found for this book. Process the book first."
        )

    # Run formatting synchronously for all chapters
    result = format_all_chapters_sync(str(book_id))

    return {
        "message": f"Formatted {result['chapters_formatted']} chapters",
        "book_id": str(book_id),
        "chapters_formatted": result['chapters_formatted']
    }


@router.post("/chapters/{chapter_id}/generate", response_model=JobRead)
async def generate_chapter_audio(
    chapter_id: str,
    voice: str = None,
    language: str = None,
    exaggeration: float = 0.8,
    cfg_weight: float = 0.3,
    temperature: float = 0.9,
    db: Session = Depends(get_db)
):
    """
    Generate audio for a chapter using TTS.

    This endpoint:
    1. Validates the chapter exists and has formatted text
    2. Creates a processing job
    3. Spawns a Celery task to generate audio via Chatterbox TTS
    4. Returns the job details for tracking

    Args:
        chapter_id: Chapter UUID
        voice: Optional voice name from Chatterbox library
        language: Optional language code (e.g., 'en', 'fr', 'es')
        exaggeration: TTS exaggeration parameter (0.0-2.0, default: 0.8)
        cfg_weight: TTS CFG weight parameter (0.0-1.0, default: 0.3)
        temperature: TTS temperature parameter (0.0-2.0, default: 0.9)
        db: Database session

    Returns:
        JobRead: Processing job details

    Raises:
        404: Chapter not found
        400: Chapter has no formatted text or is already being processed
    """
    # Check chapter exists
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with id {chapter_id} not found"
        )

    # Validate chapter has formatted text
    if not chapter.formatted_text or not chapter.formatted_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapter has no formatted text. Format the chapter first."
        )

    # Check if already being processed
    if chapter.status == "generating_audio":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chapter audio is already being generated"
        )

    # Create processing job
    job = ProcessingJob(
        book_id=chapter.book_id,
        chapter_id=chapter.id,
        job_type=JobType.GENERATE_AUDIO,
        status=JobStatus.PENDING,
        retry_count=0,
        max_retries=3,
        metadata={
            "voice": voice,
            "language": language,
            "exaggeration": exaggeration,
            "cfg_weight": cfg_weight,
            "temperature": temperature,
        }
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Run audio generation synchronously
    generate_audio_sync(
        chapter_id=str(chapter.id),
        voice=voice,
        language=language,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        temperature=temperature,
    )

    db.refresh(job)

    return job


@router.post("/books/{book_id}/chapters/generate", response_model=dict)
async def generate_all_chapters_audio(
    book_id: str,
    voice: str = None,
    language: str = None,
    db: Session = Depends(get_db)
):
    """
    Generate audio for all formatted chapters in a book.

    This endpoint spawns audio generation tasks for all chapters
    that have formatted text and are ready for TTS.

    Args:
        book_id: Book UUID
        voice: Optional voice name from Chatterbox library
        language: Optional language code
        db: Database session

    Returns:
        dict: Summary of spawned tasks

    Raises:
        404: Book not found
        400: No formatted chapters to process
    """
    # Check book exists
    from app.models.book import Book
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Check for formatted chapters
    chapters_count = db.query(Chapter).filter(
        Chapter.book_id == book_id,
        Chapter.status == "formatted"
    ).count()

    if chapters_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No formatted chapters found for this book"
        )

    # Run audio generation synchronously for all chapters
    result = generate_book_audio_sync(
        book_id=str(book_id),
        voice=voice,
        language=language,
    )

    return {
        "message": f"Generated audio for {result['chapters_count']} chapters",
        "book_id": str(book_id),
        "chapters_count": result['chapters_count'],
        "status": result['status']
    }
