import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.api.v1 import books, health, chapters, jobs, audio

# Configure logging to show in console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

settings = get_settings()
logger = logging.getLogger(__name__)

# Import models to register them with Base
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.audio_file import AudioFile
from app.models.processing_job import ProcessingJob, JobStatus


def init_db():
    """Initialize database tables using raw SQL for SQLite compatibility"""
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Only create tables if they don't exist
    if not existing_tables:
        # Create tables one by one to avoid timeout issues
        for table in Base.metadata.sorted_tables:
            if table.name not in existing_tables:
                table.create(bind=engine, checkfirst=True)


def cleanup_zombie_states():
    """
    Clean up zombie states from interrupted processing.

    This resets chapters and jobs that were left in processing states
    (formatting, generating, running, pending) when the server was stopped.
    """
    db = SessionLocal()
    try:
        # Reset chapters stuck in 'formatting' state back to 'extracted'
        formatting_chapters = db.query(Chapter).filter(
            Chapter.status == "formatting"
        ).all()

        for chapter in formatting_chapters:
            logger.warning(f"Resetting zombie chapter {chapter.id} from 'formatting' to 'extracted'")
            chapter.status = "extracted"
            chapter.error_message = "Processing was interrupted by server restart"

        # Reset chapters stuck in 'generating' state back to 'formatted'
        generating_chapters = db.query(Chapter).filter(
            Chapter.status == "generating"
        ).all()

        for chapter in generating_chapters:
            logger.warning(f"Resetting zombie chapter {chapter.id} from 'generating' to 'formatted'")
            chapter.status = "formatted"
            chapter.error_message = "Processing was interrupted by server restart"

        # Reset books stuck in processing states
        processing_books = db.query(Book).filter(
            Book.status.in_(["parsing", "formatting", "generating"])
        ).all()

        for book in processing_books:
            logger.warning(f"Resetting zombie book {book.id} from '{book.status}' to 'failed'")
            book.status = "failed"
            book.error_message = "Processing was interrupted by server restart"

        # Mark running/pending jobs as failed
        zombie_jobs = db.query(ProcessingJob).filter(
            ProcessingJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING, JobStatus.RETRYING])
        ).all()

        for job in zombie_jobs:
            logger.warning(f"Marking zombie job {job.id} ({job.job_type}) as failed")
            job.status = JobStatus.FAILED
            job.error_message = "Job was interrupted by server restart"

        db.commit()

        total_cleaned = len(formatting_chapters) + len(generating_chapters) + len(processing_books) + len(zombie_jobs)
        if total_cleaned > 0:
            logger.info(f"Cleaned up {total_cleaned} zombie states on startup")

    except Exception as e:
        logger.error(f"Error cleaning up zombie states: {e}")
        db.rollback()
    finally:
        db.close()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="BookWhisperer - Convert EPUB/TXT books to audiobooks using LLM and TTS",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=f"{settings.API_V1_PREFIX}/health", tags=["health"])
app.include_router(books.router, prefix=f"{settings.API_V1_PREFIX}/books", tags=["books"])
app.include_router(chapters.router, prefix=f"{settings.API_V1_PREFIX}", tags=["chapters"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_PREFIX}/jobs", tags=["jobs"])
app.include_router(audio.router, prefix=f"{settings.API_V1_PREFIX}", tags=["audio"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and cleanup zombie states on startup"""
    # Clean up any zombie states from interrupted processing
    cleanup_zombie_states()


@app.get("/")
async def root():
    return {
        "message": "Welcome to BookWhisperer API",
        "version": "0.1.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
