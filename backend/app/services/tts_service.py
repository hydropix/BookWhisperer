"""
Text-to-Speech service with Chatterbox integration.
Provides an abstraction layer for TTS generation with support for chunking,
voice management, and automatic error handling.
"""

import logging
import httpx
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)


class TTSConfig(BaseModel):
    """Configuration for TTS generation."""
    exaggeration: float = 0.8
    cfg_weight: float = 0.3
    temperature: float = 0.9
    voice: Optional[str] = None
    language: Optional[str] = None


class TTSChunk(BaseModel):
    """Represents a chunk of text to be converted to speech."""
    text: str
    index: int
    total_chunks: int


class TTSResult(BaseModel):
    """Result from TTS generation."""
    audio_data: bytes
    format: str = "wav"
    chunk_index: int
    total_chunks: int
    duration_seconds: Optional[float] = None


class ChatterboxTTSService:
    """
    Service for generating speech using Chatterbox TTS API.
    Supports automatic chunking, voice cloning, and multilingual generation.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 300,
        max_chunk_size: int = 5000,
    ):
        """
        Initialize Chatterbox TTS service.

        Args:
            base_url: Base URL for Chatterbox API (defaults to settings)
            timeout: Request timeout in seconds (default: 5 minutes for long texts)
            max_chunk_size: Maximum characters per chunk (default: 5000)
        """
        self.base_url = base_url or settings.CHATTERBOX_URL
        self.timeout = timeout
        self.max_chunk_size = max_chunk_size
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
        )

    async def health_check(self) -> bool:
        """
        Check if Chatterbox TTS service is available.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.client.get("/voices")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Chatterbox health check failed: {e}")
            return False

    async def list_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices from the library.

        Returns:
            List of voice dictionaries with name and metadata
        """
        try:
            response = await self.client.get("/voices")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            return []

    async def upload_voice(
        self,
        voice_file_path: Path,
        voice_name: str,
        language: Optional[str] = None,
    ) -> bool:
        """
        Upload a custom voice to the library.

        Args:
            voice_file_path: Path to voice sample file (WAV, MP3)
            voice_name: Name to store voice as
            language: Optional language code (e.g., 'en', 'fr', 'es')

        Returns:
            True if upload successful, False otherwise
        """
        try:
            with open(voice_file_path, "rb") as f:
                files = {"voice_file": (voice_file_path.name, f, "audio/wav")}
                data = {"voice_name": voice_name}
                if language:
                    data["language"] = language

                response = await self.client.post(
                    "/voices",
                    files=files,
                    data=data,
                )
                response.raise_for_status()
                logger.info(f"Voice '{voice_name}' uploaded successfully")
                return True
        except Exception as e:
            logger.error(f"Failed to upload voice '{voice_name}': {e}")
            return False

    def chunk_text(self, text: str) -> List[TTSChunk]:
        """
        Split text into chunks suitable for TTS processing.
        Splits by sentences to preserve natural speech flow.

        Args:
            text: Text to chunk

        Returns:
            List of TTSChunk objects
        """
        if len(text) <= self.max_chunk_size:
            return [TTSChunk(text=text, index=0, total_chunks=1)]

        # Split by sentences (periods, exclamation marks, question marks)
        import re
        sentences = re.split(r'([.!?]+\s+)', text)

        chunks = []
        current_chunk = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            separator = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + separator

            if len(current_chunk) + len(full_sentence) <= self.max_chunk_size:
                current_chunk += full_sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = full_sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return [
            TTSChunk(text=chunk, index=i, total_chunks=len(chunks))
            for i, chunk in enumerate(chunks)
        ]

    async def generate_speech(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
        chunk_index: int = 0,
        total_chunks: int = 1,
    ) -> TTSResult:
        """
        Generate speech from text using Chatterbox API.

        Args:
            text: Text to convert to speech
            config: TTS configuration (voice, parameters)
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks

        Returns:
            TTSResult with audio data

        Raises:
            httpx.HTTPError: If API request fails
        """
        config = config or TTSConfig()

        payload = {
            "input": text,
            "exaggeration": config.exaggeration,
            "cfg_weight": config.cfg_weight,
            "temperature": config.temperature,
        }

        if config.voice:
            payload["voice"] = config.voice
        if config.language:
            payload["language"] = config.language

        try:
            logger.info(
                f"Generating speech for chunk {chunk_index + 1}/{total_chunks} "
                f"({len(text)} chars)"
            )

            response = await self.client.post(
                "/v1/audio/speech",
                json=payload,
            )
            response.raise_for_status()

            audio_data = response.content
            logger.info(
                f"Generated audio chunk {chunk_index + 1}/{total_chunks} "
                f"({len(audio_data)} bytes)"
            )

            return TTSResult(
                audio_data=audio_data,
                format="wav",
                chunk_index=chunk_index,
                total_chunks=total_chunks,
            )

        except httpx.HTTPError as e:
            logger.error(
                f"TTS generation failed for chunk {chunk_index + 1}/{total_chunks}: {e}"
            )
            raise

    async def generate_speech_from_chunks(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
    ) -> List[TTSResult]:
        """
        Generate speech from text, automatically chunking if needed.

        Args:
            text: Text to convert to speech
            config: TTS configuration

        Returns:
            List of TTSResult objects (one per chunk)
        """
        chunks = self.chunk_text(text)
        logger.info(f"Processing text in {len(chunks)} chunks")

        results = []
        for chunk in chunks:
            result = await self.generate_speech(
                text=chunk.text,
                config=config,
                chunk_index=chunk.index,
                total_chunks=chunk.total_chunks,
            )
            results.append(result)

        return results

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Factory function for easy instantiation
def create_tts_service() -> ChatterboxTTSService:
    """
    Create a TTS service instance with default settings.

    Returns:
        ChatterboxTTSService instance
    """
    return ChatterboxTTSService()


# Singleton instance for reuse across the application
_tts_service: Optional[ChatterboxTTSService] = None


async def get_tts_service() -> ChatterboxTTSService:
    """
    Get or create the global TTS service instance.

    Returns:
        ChatterboxTTSService singleton
    """
    global _tts_service
    if _tts_service is None:
        _tts_service = create_tts_service()
    return _tts_service
