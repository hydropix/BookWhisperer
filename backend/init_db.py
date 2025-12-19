"""Script to initialize the database tables using raw SQL."""
import sqlite3
import os

DB_PATH = "bookwhisperer.db"

# SQL statements to create tables
CREATE_TABLES_SQL = """
-- Books table
CREATE TABLE IF NOT EXISTS books (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(255),
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    total_chapters INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'uploaded' NOT NULL,
    error_message TEXT,
    book_metadata TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Chapters table
CREATE TABLE IF NOT EXISTS chapters (
    id VARCHAR(36) PRIMARY KEY,
    book_id VARCHAR(36) NOT NULL,
    chapter_number INTEGER NOT NULL,
    title VARCHAR(500),
    raw_text TEXT NOT NULL,
    formatted_text TEXT,
    word_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'extracted' NOT NULL,
    excluded INTEGER DEFAULT 0 NOT NULL,
    error_message TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id VARCHAR(36) PRIMARY KEY,
    chapter_id VARCHAR(36) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size INTEGER NOT NULL,
    duration_seconds REAL,
    format VARCHAR(10) DEFAULT 'mp3' NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    tts_model VARCHAR(100),
    voice_id VARCHAR(100),
    created_at DATETIME NOT NULL,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- Processing jobs table
CREATE TABLE IF NOT EXISTS processing_jobs (
    id VARCHAR(36) PRIMARY KEY,
    book_id VARCHAR(36) NOT NULL,
    chapter_id VARCHAR(36),
    job_type VARCHAR(20) NOT NULL,
    celery_task_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    progress_percent INTEGER DEFAULT 0,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    job_metadata TEXT,
    started_at DATETIME,
    completed_at DATETIME,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (chapter_id) REFERENCES chapters(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_chapters_book_id ON chapters(book_id);
CREATE INDEX IF NOT EXISTS idx_audio_files_chapter_id ON audio_files(chapter_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_book_id ON processing_jobs(book_id);
CREATE INDEX IF NOT EXISTS idx_processing_jobs_chapter_id ON processing_jobs(chapter_id);
"""

def init_database():
    """Initialize the SQLite database with all required tables."""
    print("Initializing database...")

    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Execute all CREATE TABLE statements
    cursor.executescript(CREATE_TABLES_SQL)

    # Commit and close
    conn.commit()
    conn.close()

    print("Database initialized successfully!")

if __name__ == "__main__":
    init_database()
