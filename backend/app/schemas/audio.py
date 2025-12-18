from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class AudioFileBase(BaseModel):
    format: str = "mp3"
    chunk_index: int = 0
    total_chunks: int = 1


class AudioFileCreate(AudioFileBase):
    chapter_id: UUID
    file_path: str
    file_size: int
    duration_seconds: Optional[float] = None
    tts_model: Optional[str] = None
    voice_id: Optional[str] = None


class AudioFileRead(AudioFileBase):
    id: UUID
    chapter_id: UUID
    file_path: str
    file_size: int
    duration_seconds: Optional[float] = None
    tts_model: Optional[str] = None
    voice_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
