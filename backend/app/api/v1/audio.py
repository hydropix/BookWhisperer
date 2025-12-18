"""
API endpoints for audio file management.
Handles audio download, streaming, and bulk operations.
"""

import os
import zipfile
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audio_file import AudioFile
from app.models.chapter import Chapter
from app.models.book import Book
from app.config import settings

router = APIRouter()


@router.get("/audio/{audio_id}/download")
async def download_audio(
    audio_id: str,
    db: Session = Depends(get_db),
):
    """
    Download an audio file.

    Args:
        audio_id: AudioFile UUID
        db: Database session

    Returns:
        FileResponse with audio file

    Raises:
        404: Audio file not found
        404: File not found on disk
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with id {audio_id} not found"
        )

    file_path = Path(audio_file.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not found on disk: {file_path}"
        )

    # Get chapter info for filename
    chapter = db.query(Chapter).filter(Chapter.id == audio_file.chapter_id).first()
    if chapter and chapter.title:
        filename = f"{chapter.title}_chunk_{audio_file.chunk_index}.{audio_file.format}"
    else:
        filename = f"audio_{audio_id}.{audio_file.format}"

    # Clean filename for download
    filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.'))

    return FileResponse(
        path=str(file_path),
        media_type=f"audio/{audio_file.format}",
        filename=filename,
    )


@router.get("/audio/{audio_id}/stream")
async def stream_audio(
    audio_id: str,
    db: Session = Depends(get_db),
):
    """
    Stream an audio file.

    This endpoint supports range requests for seeking in audio players.

    Args:
        audio_id: AudioFile UUID
        db: Database session

    Returns:
        StreamingResponse with audio data

    Raises:
        404: Audio file not found
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with id {audio_id} not found"
        )

    file_path = Path(audio_file.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file not found on disk: {file_path}"
        )

    def iterfile():
        with open(file_path, mode="rb") as f:
            yield from f

    return StreamingResponse(
        iterfile(),
        media_type=f"audio/{audio_file.format}",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(audio_file.file_size),
        }
    )


@router.get("/chapters/{chapter_id}/audio")
async def list_chapter_audio(
    chapter_id: str,
    db: Session = Depends(get_db),
):
    """
    List all audio files for a chapter.

    Args:
        chapter_id: Chapter UUID
        db: Database session

    Returns:
        List of audio file records

    Raises:
        404: Chapter not found
    """
    chapter = db.query(Chapter).filter(Chapter.id == chapter_id).first()
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter with id {chapter_id} not found"
        )

    audio_files = (
        db.query(AudioFile)
        .filter(AudioFile.chapter_id == chapter_id)
        .order_by(AudioFile.chunk_index)
        .all()
    )

    return {
        "chapter_id": str(chapter_id),
        "audio_files": [
            {
                "id": str(af.id),
                "file_path": af.file_path,
                "file_size": af.file_size,
                "format": af.format,
                "chunk_index": af.chunk_index,
                "total_chunks": af.total_chunks,
                "duration_seconds": af.duration_seconds,
                "download_url": f"/api/v1/audio/{af.id}/download",
                "stream_url": f"/api/v1/audio/{af.id}/stream",
            }
            for af in audio_files
        ],
        "total_files": len(audio_files),
    }


@router.get("/books/{book_id}/audio/download")
async def download_book_audio(
    book_id: str,
    db: Session = Depends(get_db),
):
    """
    Download all audio files for a book as a ZIP archive.

    This creates a ZIP file containing all chapter audio files
    organized by chapter number.

    Args:
        book_id: Book UUID
        db: Database session

    Returns:
        FileResponse with ZIP archive

    Raises:
        404: Book not found
        400: No audio files found for book
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Get all chapters with audio files
    chapters = (
        db.query(Chapter)
        .filter(Chapter.book_id == book_id)
        .order_by(Chapter.chapter_number)
        .all()
    )

    if not chapters:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No chapters found for this book"
        )

    # Collect all audio files
    all_audio_files = []
    for chapter in chapters:
        audio_files = (
            db.query(AudioFile)
            .filter(AudioFile.chapter_id == chapter.id)
            .order_by(AudioFile.chunk_index)
            .all()
        )
        if audio_files:
            all_audio_files.extend([(chapter, af) for af in audio_files])

    if not all_audio_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio files found for this book"
        )

    # Create temporary ZIP file
    import tempfile
    temp_dir = Path(tempfile.gettempdir())
    zip_filename = f"{book.title or book_id}_audiobook.zip"
    zip_filename = "".join(c for c in zip_filename if c.isalnum() or c in (' ', '_', '-', '.'))
    zip_path = temp_dir / zip_filename

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for chapter, audio_file in all_audio_files:
                file_path = Path(audio_file.file_path)
                if not file_path.exists():
                    continue

                # Create organized path in ZIP
                chapter_num = f"{chapter.chapter_number:03d}"
                chapter_title = chapter.title or f"Chapter_{chapter_num}"
                chapter_title = "".join(c for c in chapter_title if c.isalnum() or c in (' ', '_', '-'))

                if audio_file.total_chunks > 1:
                    archive_name = f"{chapter_num}_{chapter_title}/chunk_{audio_file.chunk_index:03d}.{audio_file.format}"
                else:
                    archive_name = f"{chapter_num}_{chapter_title}.{audio_file.format}"

                zipf.write(file_path, archive_name)

        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=zip_filename,
            headers={
                "Content-Disposition": f'attachment; filename="{zip_filename}"'
            }
        )

    except Exception as e:
        if zip_path.exists():
            zip_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ZIP archive: {str(e)}"
        )


@router.delete("/audio/{audio_id}")
async def delete_audio(
    audio_id: str,
    db: Session = Depends(get_db),
):
    """
    Delete an audio file.

    Args:
        audio_id: AudioFile UUID
        db: Database session

    Returns:
        Success message

    Raises:
        404: Audio file not found
    """
    audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with id {audio_id} not found"
        )

    # Delete file from disk
    file_path = Path(audio_file.file_path)
    if file_path.exists():
        file_path.unlink()

    # Delete from database
    db.delete(audio_file)
    db.commit()

    return {"message": f"Audio file {audio_id} deleted successfully"}
