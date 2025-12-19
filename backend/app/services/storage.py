import os
import shutil
from pathlib import Path
from typing import BinaryIO
import uuid
from app.config import get_settings

settings = get_settings()


class StorageService:
    """Service for handling file storage operations"""

    @staticmethod
    def save_upload(file: BinaryIO, filename: str) -> tuple[str, str]:
        """
        Save uploaded file to storage

        Args:
            file: File object to save
            filename: Original filename

        Returns:
            tuple: (file_path, unique_filename)
        """
        # Ensure upload directory exists
        upload_dir = Path(settings.UPLOAD_STORAGE_PATH)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / unique_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file, buffer)

        return str(file_path), unique_filename

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete file from storage

        Args:
            file_path: Path to file to delete

        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes

        Args:
            file_path: Path to file

        Returns:
            int: File size in bytes
        """
        if os.path.exists(file_path):
            return os.path.getsize(file_path)
        return 0

    @staticmethod
    def ensure_audio_dir(book_id: str) -> Path:
        """
        Ensure audio directory exists for a book

        Args:
            book_id: Book UUID

        Returns:
            Path: Path to book's audio directory
        """
        audio_dir = Path(settings.AUDIO_STORAGE_PATH) / str(book_id)
        audio_dir.mkdir(parents=True, exist_ok=True)
        return audio_dir
