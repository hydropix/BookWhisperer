from sqlalchemy import Column, String, Integer, DateTime, Enum, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class BookStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    FORMATTING = "formatting"
    FORMATTED = "formatted"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class FileType(str, enum.Enum):
    EPUB = "epub"
    TXT = "txt"


class Book(Base):
    __tablename__ = "books"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    author = Column(String(255))
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    total_chapters = Column(Integer, default=0)
    status = Column(Enum(BookStatus), default=BookStatus.UPLOADED, nullable=False)
    error_message = Column(Text)
    book_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chapters = relationship("Chapter", back_populates="book", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="book", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Book(id={self.id}, title={self.title}, status={self.status})>"
