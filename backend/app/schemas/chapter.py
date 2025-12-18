from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.chapter import ChapterStatus


class ChapterBase(BaseModel):
    title: Optional[str] = None
    chapter_number: int


class ChapterCreate(ChapterBase):
    book_id: UUID
    raw_text: str
    word_count: int = 0
    character_count: int = 0


class ChapterRead(ChapterBase):
    id: UUID
    book_id: UUID
    raw_text: str
    formatted_text: Optional[str] = None
    word_count: int
    character_count: int
    status: ChapterStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChapterList(BaseModel):
    chapters: list[ChapterRead]
    total: int


class ChapterUpdate(BaseModel):
    title: Optional[str] = None
    formatted_text: Optional[str] = None
    status: Optional[ChapterStatus] = None
    error_message: Optional[str] = None
