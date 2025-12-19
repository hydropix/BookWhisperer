from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    duration_seconds = Column(Float)
    format = Column(String(10), default="mp3", nullable=False)
    chunk_index = Column(Integer, default=0)
    total_chunks = Column(Integer, default=1)
    tts_model = Column(String(100))
    voice_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    chapter = relationship("Chapter", back_populates="audio_files")

    def __repr__(self):
        return f"<AudioFile(id={self.id}, chapter_id={self.chapter_id}, chunk={self.chunk_index}/{self.total_chunks})>"
