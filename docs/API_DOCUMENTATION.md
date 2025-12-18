# BookWhisperer API Documentation

Complete API reference for the BookWhisperer audiobook generation platform.

**Base URL:** `http://localhost:8000/api/v1`

**Interactive Documentation:** `http://localhost:8000/docs` (Swagger UI)

---

## Table of Contents

- [Authentication](#authentication)
- [Books](#books)
- [Chapters](#chapters)
- [Audio](#audio)
- [Jobs](#jobs)
- [Health](#health)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Authentication

Currently, the API does not require authentication. This will be added in a future release for multi-user support.

---

## Books

### Upload a Book

Upload an EPUB or TXT file and automatically trigger parsing.

**Endpoint:** `POST /books/upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file` (required): EPUB or TXT file
  - `title` (optional): Book title (auto-extracted if not provided)
  - `author` (optional): Book author

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/books/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@mybook.epub" \
  -F "title=The Great Gatsby" \
  -F "author=F. Scott Fitzgerald"
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "file_name": "mybook.epub",
  "file_path": "storage/uploads/550e8400-e29b-41d4-a716-446655440000.epub",
  "file_type": "epub",
  "total_chapters": 0,
  "status": "pending",
  "error_message": null,
  "metadata": {},
  "created_at": "2024-12-18T10:30:00Z",
  "updated_at": "2024-12-18T10:30:00Z"
}
```

---

### List Books

Retrieve a paginated list of all uploaded books.

**Endpoint:** `GET /books`

**Query Parameters:**
- `page` (optional, default: 1): Page number
- `page_size` (optional, default: 20, max: 100): Items per page

**Example:**
```bash
curl "http://localhost:8000/api/v1/books?page=1&page_size=20"
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "The Great Gatsby",
      "author": "F. Scott Fitzgerald",
      "file_name": "mybook.epub",
      "file_type": "epub",
      "total_chapters": 9,
      "status": "parsed",
      "error_message": null,
      "metadata": {
        "language": "en"
      },
      "created_at": "2024-12-18T10:30:00Z",
      "updated_at": "2024-12-18T10:35:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### Get Book Details

Retrieve detailed information about a specific book.

**Endpoint:** `GET /books/{book_id}`

**Example:**
```bash
curl "http://localhost:8000/api/v1/books/550e8400-e29b-41d4-a716-446655440000"
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "file_name": "mybook.epub",
  "file_path": "storage/uploads/550e8400-e29b-41d4-a716-446655440000.epub",
  "file_type": "epub",
  "total_chapters": 9,
  "status": "parsed",
  "error_message": null,
  "metadata": {
    "language": "en",
    "publisher": "Scribner"
  },
  "created_at": "2024-12-18T10:30:00Z",
  "updated_at": "2024-12-18T10:35:00Z"
}
```

---

### Update Book

Update book metadata (title, author).

**Endpoint:** `PATCH /books/{book_id}`

**Request Body:**
```json
{
  "title": "The Great Gatsby (Updated)",
  "author": "F. Scott Fitzgerald"
}
```

**Example:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/books/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"title":"The Great Gatsby (Updated)"}'
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "The Great Gatsby (Updated)",
  "author": "F. Scott Fitzgerald",
  ...
}
```

---

### Delete Book

Delete a book and all associated data (chapters, audio files, jobs).

**Endpoint:** `DELETE /books/{book_id}`

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/books/550e8400-e29b-41d4-a716-446655440000"
```

**Response:** `204 No Content`

---

### Process Book

Manually trigger book processing (normally done automatically on upload).

**Endpoint:** `POST /books/{book_id}/process`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/books/550e8400-e29b-41d4-a716-446655440000/process"
```

**Response:** `200 OK`
```json
{
  "message": "Processing started",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "celery-task-id-123"
}
```

---

## Chapters

### List Chapters

Get all chapters for a specific book.

**Endpoint:** `GET /books/{book_id}/chapters`

**Example:**
```bash
curl "http://localhost:8000/api/v1/books/550e8400-e29b-41d4-a716-446655440000/chapters"
```

**Response:** `200 OK`
```json
{
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_chapters": 9,
  "chapters": [
    {
      "id": "chapter-id-1",
      "book_id": "550e8400-e29b-41d4-a716-446655440000",
      "chapter_number": 1,
      "title": "Chapter I",
      "raw_text": "In my younger and more vulnerable years...",
      "formatted_text": null,
      "word_count": 4291,
      "character_count": 24512,
      "status": "parsed",
      "error_message": null,
      "created_at": "2024-12-18T10:35:00Z",
      "updated_at": "2024-12-18T10:35:00Z"
    }
  ]
}
```

---

### Get Chapter Details

Retrieve detailed information about a specific chapter.

**Endpoint:** `GET /chapters/{chapter_id}`

**Example:**
```bash
curl "http://localhost:8000/api/v1/chapters/chapter-id-1"
```

**Response:** `200 OK`
```json
{
  "id": "chapter-id-1",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "chapter_number": 1,
  "title": "Chapter I",
  "raw_text": "In my younger and more vulnerable years...",
  "formatted_text": "In my younger and more vulnerable years...",
  "word_count": 4291,
  "character_count": 24512,
  "status": "formatted",
  "error_message": null,
  "created_at": "2024-12-18T10:35:00Z",
  "updated_at": "2024-12-18T10:40:00Z"
}
```

---

### Format Single Chapter

Format a single chapter using the LLM.

**Endpoint:** `POST /chapters/{chapter_id}/format`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/chapters/chapter-id-1/format"
```

**Response:** `200 OK`
```json
{
  "id": "job-id-123",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "chapter_id": "chapter-id-1",
  "job_type": "format_chapter",
  "status": "pending",
  "progress_percent": 0,
  "celery_task_id": "celery-task-id-456",
  "error_message": null,
  "retry_count": 0,
  "max_retries": 3,
  "metadata": {},
  "started_at": null,
  "completed_at": null,
  "created_at": "2024-12-18T10:40:00Z",
  "updated_at": "2024-12-18T10:40:00Z"
}
```

---

### Format All Chapters

Format all chapters in a book using the LLM.

**Endpoint:** `POST /books/{book_id}/chapters/format`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/books/550e8400-e29b-41d4-a716-446655440000/chapters/format"
```

**Response:** `200 OK`
```json
{
  "message": "Started formatting 9 chapters",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "celery-group-id-789",
  "chapters_count": 9
}
```

---

### Generate Audio for Chapter

Generate audio for a single formatted chapter (requires Phase 4 TTS integration).

**Endpoint:** `POST /chapters/{chapter_id}/generate`

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/chapters/chapter-id-1/generate"
```

**Response:** `200 OK`
```json
{
  "id": "job-id-789",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "chapter_id": "chapter-id-1",
  "job_type": "generate_audio",
  "status": "pending",
  "progress_percent": 0,
  "celery_task_id": "celery-task-id-999",
  "created_at": "2024-12-18T10:50:00Z"
}
```

---

## Audio

### Download Audio File

Download a generated audio file.

**Endpoint:** `GET /audio/{audio_id}/download`

**Example:**
```bash
curl -O "http://localhost:8000/api/v1/audio/audio-id-1/download"
```

**Response:** `200 OK`
- Content-Type: `audio/mpeg`
- Content-Disposition: `attachment; filename="chapter-1.mp3"`

---

### Stream Audio File

Stream an audio file for playback.

**Endpoint:** `GET /audio/{audio_id}/stream`

**Example:**
```bash
curl "http://localhost:8000/api/v1/audio/audio-id-1/stream"
```

**Response:** `200 OK`
- Content-Type: `audio/mpeg`
- Supports range requests for seeking

---

## Jobs

### Get Job Status

Retrieve the current status of a processing job.

**Endpoint:** `GET /jobs/{job_id}`

**Example:**
```bash
curl "http://localhost:8000/api/v1/jobs/job-id-123"
```

**Response:** `200 OK`
```json
{
  "id": "job-id-123",
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "chapter_id": "chapter-id-1",
  "job_type": "format_chapter",
  "status": "processing",
  "progress_percent": 45,
  "celery_task_id": "celery-task-id-456",
  "error_message": null,
  "retry_count": 0,
  "max_retries": 3,
  "metadata": {
    "total_chunks": 10,
    "current_chunk": 5
  },
  "started_at": "2024-12-18T10:40:05Z",
  "completed_at": null,
  "created_at": "2024-12-18T10:40:00Z",
  "updated_at": "2024-12-18T10:40:30Z"
}
```

---

### Get All Jobs for a Book

Retrieve all processing jobs for a specific book.

**Endpoint:** `GET /jobs/books/{book_id}/jobs`

**Example:**
```bash
curl "http://localhost:8000/api/v1/jobs/books/550e8400-e29b-41d4-a716-446655440000/jobs"
```

**Response:** `200 OK`
```json
{
  "book_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_jobs": 10,
  "jobs": [
    {
      "id": "job-id-1",
      "job_type": "parse_book",
      "status": "completed",
      "progress_percent": 100,
      "completed_at": "2024-12-18T10:35:00Z"
    },
    {
      "id": "job-id-2",
      "job_type": "format_chapter",
      "status": "processing",
      "progress_percent": 45
    }
  ]
}
```

---

### Get Job by Celery Task ID

Find a job by its Celery task ID.

**Endpoint:** `GET /jobs/celery/{celery_task_id}`

**Example:**
```bash
curl "http://localhost:8000/api/v1/jobs/celery/celery-task-id-456"
```

**Response:** `200 OK`
```json
{
  "id": "job-id-123",
  "job_type": "format_chapter",
  "status": "processing",
  "celery_task_id": "celery-task-id-456",
  ...
}
```

---

## Health

### API Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Example:**
```bash
curl "http://localhost:8000/api/v1/health"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-12-18T10:30:00Z"
}
```

---

### Database Health Check

Check database connection.

**Endpoint:** `GET /health/db`

**Example:**
```bash
curl "http://localhost:8000/api/v1/health/db"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "database",
  "details": {
    "connected": true,
    "database": "bookwhisperer"
  }
}
```

---

### Ollama Health Check

Check Ollama LLM service connection.

**Endpoint:** `GET /health/ollama`

**Example:**
```bash
curl "http://localhost:8000/api/v1/health/ollama"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "ollama",
  "details": {
    "url": "http://ollama:11434",
    "model": "llama2",
    "available": true
  }
}
```

---

### TTS Health Check

Check Chatterbox TTS service connection.

**Endpoint:** `GET /health/tts`

**Example:**
```bash
curl "http://localhost:8000/api/v1/health/tts"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "tts",
  "details": {
    "url": "http://chatterbox:4123",
    "available": true,
    "voices": 5
  }
}
```

---

### All Services Health Check

Check all services at once.

**Endpoint:** `GET /health/all`

**Example:**
```bash
curl "http://localhost:8000/api/v1/health/all"
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "ollama": "healthy",
    "tts": "healthy",
    "redis": "healthy"
  },
  "timestamp": "2024-12-18T10:30:00Z"
}
```

---

## Error Handling

All API errors follow a consistent format:

```json
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-12-18T10:30:00Z"
}
```

### Common HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Request successful, no content to return
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate operation)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - Service temporarily unavailable

### Example Error Response

```json
{
  "detail": "Book not found",
  "error_code": "BOOK_NOT_FOUND",
  "timestamp": "2024-12-18T10:30:00Z"
}
```

---

## Rate Limiting

Currently, there are no rate limits enforced. This will be added in future releases for production deployments.

**Recommended limits for production:**
- 100 requests per minute per IP for read operations
- 10 requests per minute per IP for write operations
- 5 concurrent book uploads per user

---

## Status Values

### Book Status
- `pending` - Book uploaded, waiting to be parsed
- `parsing` - Book is being parsed
- `parsed` - Parsing complete, chapters extracted
- `formatting` - Chapters are being formatted
- `generating` - Audio is being generated
- `completed` - All processing complete
- `failed` - Processing failed

### Chapter Status
- `pending` - Chapter extracted, not yet formatted
- `formatting` - LLM formatting in progress
- `formatted` - Formatting complete
- `generating` - Audio generation in progress
- `completed` - Audio generation complete
- `failed` - Processing failed

### Job Status
- `pending` - Job queued, not yet started
- `processing` - Job currently running
- `completed` - Job finished successfully
- `failed` - Job failed (check error_message)

---

## Pagination

List endpoints support pagination:

**Parameters:**
- `page` - Page number (starts at 1)
- `page_size` - Items per page (max 100)

**Response includes:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

---

## Timestamps

All timestamps are in ISO 8601 format (UTC):
```
2024-12-18T10:30:00Z
```

---

## Best Practices

1. **Poll for job status** - Use the jobs endpoints to track long-running operations
2. **Handle retries** - Implement exponential backoff for failed requests
3. **Check health endpoints** - Verify service availability before critical operations
4. **Use pagination** - Don't fetch all items at once for large datasets
5. **Validate uploads** - Check file type and size before uploading
6. **Monitor progress** - Use the progress_percent field to track job completion

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/BookWhisperer/issues
- Documentation: See README.md and docs/USER_GUIDE.md
