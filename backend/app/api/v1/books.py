from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import shutil

from app.database import get_db
from app.models.book import Book, FileType, BookStatus
from app.schemas.book import BookRead, BookList, BookUpdate
from app.services.storage import StorageService
from app.config import get_settings
from app.tasks.book_tasks import parse_book_task

router = APIRouter()
settings = get_settings()
storage_service = StorageService()


@router.post("/upload", response_model=BookRead, status_code=status.HTTP_201_CREATED)
async def upload_book(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload a book file (EPUB or TXT)

    Args:
        file: The book file to upload
        title: Book title (optional, will be extracted from file if not provided)
        author: Book author (optional)
        db: Database session

    Returns:
        BookRead: Created book record
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in [".epub", ".txt"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only EPUB and TXT files are supported."
        )

    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to beginning

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB."
        )

    # Save file
    try:
        file_path, unique_filename = storage_service.save_upload(file.file, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Determine file type
    file_type = FileType.EPUB if file_ext == ".epub" else FileType.TXT

    # Use provided title or filename
    book_title = title or Path(file.filename).stem

    # Create book record
    book = Book(
        title=book_title,
        author=author,
        file_name=file.filename,
        file_path=file_path,
        file_type=file_type,
        status=BookStatus.UPLOADED
    )

    db.add(book)
    db.commit()
    db.refresh(book)

    # Automatically trigger parsing task
    parse_book_task.delay(str(book.id))

    return book


@router.get("", response_model=BookList)
async def list_books(
    page: int = 1,
    page_size: int = 20,
    status: Optional[BookStatus] = None,
    db: Session = Depends(get_db)
):
    """
    List all books with pagination

    Args:
        page: Page number (starts at 1)
        page_size: Number of items per page
        status: Filter by book status (optional)
        db: Database session

    Returns:
        BookList: Paginated list of books
    """
    # Build query
    query = db.query(Book)
    if status:
        query = query.filter(Book.status == status)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    books = query.order_by(Book.created_at.desc()).offset(offset).limit(page_size).all()

    return BookList(
        books=books,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{book_id}", response_model=BookRead)
async def get_book(book_id: str, db: Session = Depends(get_db)):
    """
    Get a specific book by ID

    Args:
        book_id: Book UUID
        db: Database session

    Returns:
        BookRead: Book details
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )
    return book


@router.patch("/{book_id}", response_model=BookRead)
async def update_book(
    book_id: str,
    book_update: BookUpdate,
    db: Session = Depends(get_db)
):
    """
    Update book details

    Args:
        book_id: Book UUID
        book_update: Fields to update
        db: Database session

    Returns:
        BookRead: Updated book
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Update fields
    update_data = book_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(book, field, value)

    db.commit()
    db.refresh(book)

    return book


@router.post("/{book_id}/process", response_model=BookRead)
async def process_book(book_id: str, db: Session = Depends(get_db)):
    """
    Start processing a book (parse and extract chapters)

    Args:
        book_id: Book UUID
        db: Database session

    Returns:
        BookRead: Book with updated status
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Check if book is already being processed
    if book.status in [BookStatus.PARSING, BookStatus.FORMATTING, BookStatus.GENERATING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book is already being processed (status: {book.status})"
        )

    # Trigger parsing task
    parse_book_task.delay(book_id)

    # Update status
    book.status = BookStatus.PARSING
    db.commit()
    db.refresh(book)

    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: str, db: Session = Depends(get_db)):
    """
    Delete a book and its associated files

    Args:
        book_id: Book UUID
        db: Database session
    """
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with id {book_id} not found"
        )

    # Delete uploaded file
    storage_service.delete_file(book.file_path)

    # Delete audio directory if exists
    audio_dir = Path(settings.AUDIO_DIR) / str(book.id)
    if audio_dir.exists():
        shutil.rmtree(audio_dir)

    # Delete book record (cascades to chapters, audio_files, jobs)
    db.delete(book)
    db.commit()

    return None
