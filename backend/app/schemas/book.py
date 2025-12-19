from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.book import BookStatus, FileType


class BookBase(BaseModel):
    title: str
    author: Optional[str] = None


class BookCreate(BookBase):
    file_name: str
    file_path: str
    file_type: FileType


class BookRead(BookBase):
    id: UUID
    file_name: str
    file_path: str
    file_type: FileType
    total_chapters: int
    status: BookStatus
    error_message: Optional[str] = None
    book_metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BookList(BaseModel):
    books: list[BookRead]
    total: int
    page: int
    page_size: int


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    status: Optional[BookStatus] = None
    total_chapters: Optional[int] = None
    error_message: Optional[str] = None
    book_metadata: Optional[Dict[str, Any]] = None
