"""
Tasks Module

Contains synchronous tasks for book processing.
"""

from app.tasks.book_tasks import parse_book_sync
from app.tasks.chapter_tasks import format_chapter_sync, format_all_chapters_sync
from app.tasks.audio_tasks import generate_audio_sync, generate_book_audio_sync

__all__ = [
    "parse_book_sync",
    "format_chapter_sync",
    "format_all_chapters_sync",
    "generate_audio_sync",
    "generate_book_audio_sync",
]
