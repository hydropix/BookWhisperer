# Chatterbox TTS Integration

This document describes the integration of Chatterbox TTS into BookWhisperer for audio generation.

## Overview

BookWhisperer uses [Chatterbox TTS](https://github.com/travisvn/chatterbox-tts-api) to convert formatted text into high-quality speech. Chatterbox is an open-source, state-of-the-art text-to-speech system with support for multiple languages and voice cloning.

## Features

- **Multilingual Support**: 22 languages including English, Spanish, French, German, Japanese, and more
- **Voice Cloning**: Upload custom voice samples for personalized narration
- **Automatic Chunking**: Handles long texts by splitting into manageable chunks
- **Streaming Support**: Stream audio for real-time playback
- **High Quality**: Uses the Chatterbox-Turbo model for natural-sounding speech

## Architecture

### Components

1. **TTS Service** (`app/services/tts_service.py`)
   - Abstraction layer for Chatterbox API
   - Handles text chunking and API communication
   - Supports voice management and configuration

2. **Audio Tasks** (`app/tasks/audio_tasks.py`)
   - Celery tasks for async audio generation
   - `generate_audio_task`: Generate audio for a single chapter
   - `generate_book_audio_task`: Generate audio for all chapters in a book

3. **Audio API** (`app/api/v1/audio.py`)
   - Download and stream audio files
   - List audio files for chapters
   - Download complete audiobooks as ZIP archives

## Configuration

### Environment Variables

```bash
# Chatterbox TTS Configuration
CHATTERBOX_URL=http://localhost:4123
TTS_MAX_CHUNK_SIZE=5000  # Max characters per TTS request
```

### Docker Compose

The Chatterbox service is included in `docker-compose.yml`:

```yaml
chatterbox:
  image: travisvn/chatterbox-tts-api:latest
  ports:
    - "4123:4123"
  environment:
    - DEVICE=cpu  # Use 'cuda' for GPU acceleration
  volumes:
    - chatterbox_data:/app/voices
```

## Usage

### API Endpoints

#### Generate Audio for a Chapter

```bash
POST /api/v1/chapters/{chapter_id}/generate
```

**Parameters:**
- `voice` (optional): Voice name from library
- `language` (optional): Language code (e.g., 'en', 'fr', 'es')
- `exaggeration` (optional): TTS exaggeration (0.0-2.0, default: 0.8)
- `cfg_weight` (optional): CFG weight (0.0-1.0, default: 0.3)
- `temperature` (optional): Temperature (0.0-2.0, default: 0.9)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/chapters/{chapter_id}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "voice": "narrator",
    "language": "en",
    "exaggeration": 0.8
  }'
```

#### Generate Audio for All Chapters

```bash
POST /api/v1/books/{book_id}/chapters/generate
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/books/{book_id}/chapters/generate?voice=narrator&language=en"
```

#### Download Audio File

```bash
GET /api/v1/audio/{audio_id}/download
```

#### Stream Audio

```bash
GET /api/v1/audio/{audio_id}/stream
```

#### Download Complete Audiobook

```bash
GET /api/v1/books/{book_id}/audio/download
```

Returns a ZIP archive containing all chapter audio files.

### Python SDK Example

```python
from app.services.tts_service import get_tts_service, TTSConfig

async def generate_audio_example():
    async with await get_tts_service() as tts:
        # Configure TTS
        config = TTSConfig(
            voice="narrator",
            language="en",
            exaggeration=0.8,
            cfg_weight=0.3,
            temperature=0.9,
        )

        # Generate speech
        text = "Once upon a time, in a land far away..."
        results = await tts.generate_speech_from_chunks(
            text=text,
            config=config,
        )

        # Process results
        for result in results:
            print(f"Generated chunk {result.chunk_index + 1}/{result.total_chunks}")
            print(f"Audio size: {len(result.audio_data)} bytes")
```

## Voice Management

### Upload Custom Voice

```python
from pathlib import Path
from app.services.tts_service import get_tts_service

async def upload_voice():
    async with await get_tts_service() as tts:
        voice_path = Path("path/to/voice_sample.wav")
        success = await tts.upload_voice(
            voice_file_path=voice_path,
            voice_name="my_narrator",
            language="en",
        )
        print(f"Upload successful: {success}")
```

### List Available Voices

```python
async def list_voices():
    async with await get_tts_service() as tts:
        voices = await tts.list_voices()
        for voice in voices:
            print(f"Voice: {voice['name']}, Language: {voice.get('language')}")
```

## Text Chunking

The TTS service automatically splits long texts into chunks to handle API limitations and memory constraints.

### Chunking Strategy

1. **Sentence-Based**: Splits on sentence boundaries (`.`, `!`, `?`)
2. **Max Size**: Default 5000 characters per chunk
3. **Preserves Context**: Ensures natural speech flow across chunks
4. **No Overlap**: Unlike LLM chunking, TTS chunks don't overlap

### Example

```python
from app.services.tts_service import ChatterboxTTSService

service = ChatterboxTTSService(max_chunk_size=5000)
text = "Your very long book chapter text here..."
chunks = service.chunk_text(text)

for chunk in chunks:
    print(f"Chunk {chunk.index + 1}/{chunk.total_chunks}: {len(chunk.text)} chars")
```

## Workflow

### Complete Pipeline

1. **Upload Book** → Parse chapters
2. **Format Chapters** → Clean text with LLM
3. **Generate Audio** → Convert to speech with TTS
4. **Download** → Get individual files or complete ZIP

```
EPUB/TXT → Parse → Format (LLM) → Generate (TTS) → Download
```

### Status Tracking

Each audio generation task creates a `ProcessingJob` that can be tracked:

```bash
GET /api/v1/jobs/{job_id}
```

**Job statuses:**
- `pending`: Task queued but not started
- `running`: Currently processing
- `completed`: Successfully finished
- `failed`: Error occurred

## Performance Considerations

### GPU Acceleration

For faster audio generation, use GPU acceleration:

```yaml
chatterbox:
  environment:
    - DEVICE=cuda
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Concurrent Processing

Celery workers can process multiple chapters in parallel:

```bash
celery -A app.tasks.celery_app worker --concurrency=4
```

### Storage

Audio files are stored in `storage/audio/{book_id}/{chapter_id}/`:
- Single file: `chapter_{id}.wav`
- Multiple chunks: `chapter_{id}_chunk_{index}.wav`

## Error Handling

### Retry Logic

Audio generation tasks automatically retry on failure:
- **Max retries**: 3
- **Delay**: Exponential backoff (60s, 120s, 240s)

### Common Issues

1. **Chatterbox Not Available**
   - Check service is running: `GET /api/v1/health/tts`
   - Verify Docker container is up: `docker ps | grep chatterbox`

2. **Out of Memory**
   - Reduce `TTS_MAX_CHUNK_SIZE`
   - Increase container memory limits

3. **Slow Generation**
   - Enable GPU acceleration
   - Reduce concurrent Celery workers
   - Consider using smaller chunks

## Testing

Run TTS integration tests:

```bash
pytest backend/tests/test_tts_service.py -v
```

## Supported Languages

Chatterbox supports 22 languages with language-aware voice cloning:

- Arabic (ar)
- Danish (da)
- German (de)
- Greek (el)
- English (en)
- Spanish (es)
- Finnish (fi)
- French (fr)
- Hebrew (he)
- Hindi (hi)
- Italian (it)
- Japanese (ja)
- Korean (ko)
- Malay (ms)
- Dutch (nl)
- Norwegian (no)
- Polish (pl)
- Portuguese (pt)
- Russian (ru)
- Swedish (sv)
- Swahili (sw)
- Turkish (tr)

## Advanced Features

### Paralinguistic Tags

Chatterbox-Turbo supports special tags for enhanced realism:

```python
text = "He laughed [laugh] at the joke. Then he coughed [cough]."
```

Available tags: `[laugh]`, `[chuckle]`, `[cough]`, and more.

### Voice Parameters

Fine-tune voice characteristics:

- **exaggeration** (0.0-2.0): Voice expressiveness
- **cfg_weight** (0.0-1.0): Classifier-free guidance strength
- **temperature** (0.0-2.0): Output randomness

## Resources

- [Chatterbox TTS API GitHub](https://github.com/travisvn/chatterbox-tts-api)
- [Chatterbox Official Website](https://chatterboxtts.com/)
- [Resemble AI Chatterbox](https://www.resemble.ai/chatterbox/)
- [API Documentation](https://chatterboxtts.com/docs)
