from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ChapterStatus(str, enum.Enum):
    EXTRACTED = "extracted"
    FORMATTING = "formatting"
    FORMATTED = "formatted"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    book_id = Column(String(36), ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    title = Column(String(500))
    raw_text = Column(Text, nullable=False)
    formatted_text = Column(Text)
    word_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    status = Column(Enum(ChapterStatus), default=ChapterStatus.EXTRACTED, nullable=False)
    excluded = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    book = relationship("Book", back_populates="chapters")
    audio_files = relationship("AudioFile", back_populates="chapter", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chapter(id={self.id}, book_id={self.book_id}, number={self.chapter_number}, status={self.status})>"
