"""
Unit tests for TTS service.
Tests the Chatterbox TTS integration with mocked API calls.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.services.tts_service import (
    ChatterboxTTSService,
    TTSConfig,
    TTSChunk,
    TTSResult,
)


@pytest.fixture
def tts_service():
    """Create a TTS service instance for testing."""
    return ChatterboxTTSService(
        base_url="http://localhost:4123",
        timeout=60,
        max_chunk_size=100,  # Small for testing
    )


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    with patch("app.services.tts_service.httpx.AsyncClient") as mock_client:
        yield mock_client


class TestChatterboxTTSService:
    """Test cases for ChatterboxTTSService."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, tts_service, mock_httpx_client):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

        tts_service.client = mock_client_instance
        result = await tts_service.health_check()

        assert result is True
        mock_client_instance.get.assert_called_once_with("/voices")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, tts_service, mock_httpx_client):
        """Test failed health check."""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = Exception("Connection failed")

        tts_service.client = mock_client_instance
        result = await tts_service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_list_voices(self, tts_service, mock_httpx_client):
        """Test listing available voices."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"name": "voice1", "language": "en"},
            {"name": "voice2", "language": "fr"},
        ]

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        tts_service.client = mock_client_instance

        voices = await tts_service.list_voices()

        assert len(voices) == 2
        assert voices[0]["name"] == "voice1"
        assert voices[1]["language"] == "fr"

    def test_chunk_text_small(self, tts_service):
        """Test chunking with text smaller than max size."""
        text = "This is a short text."
        chunks = tts_service.chunk_text(text)

        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0
        assert chunks[0].total_chunks == 1

    def test_chunk_text_large(self, tts_service):
        """Test chunking with text larger than max size."""
        # Create text that will be split into multiple chunks
        sentences = [f"This is sentence {i}. " for i in range(20)]
        text = "".join(sentences)

        chunks = tts_service.chunk_text(text)

        # Should create multiple chunks
        assert len(chunks) > 1

        # All chunks should have correct index and total
        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert chunk.total_chunks == len(chunks)
            assert len(chunk.text) <= tts_service.max_chunk_size

    def test_chunk_text_preserves_sentences(self, tts_service):
        """Test that chunking preserves sentence boundaries."""
        text = "First sentence. Second sentence. Third sentence."
        chunks = tts_service.chunk_text(text)

        # Each chunk should end with sentence punctuation or be the last chunk
        for i, chunk in enumerate(chunks[:-1]):
            assert chunk.text.rstrip().endswith((".", "!", "?"))

    @pytest.mark.asyncio
    async def test_generate_speech_success(self, tts_service, mock_httpx_client):
        """Test successful speech generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_audio_data"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        tts_service.client = mock_client_instance

        config = TTSConfig(
            voice="test_voice",
            language="en",
            exaggeration=0.8,
        )

        result = await tts_service.generate_speech(
            text="Hello world",
            config=config,
            chunk_index=0,
            total_chunks=1,
        )

        assert isinstance(result, TTSResult)
        assert result.audio_data == b"fake_audio_data"
        assert result.format == "wav"
        assert result.chunk_index == 0
        assert result.total_chunks == 1

        # Verify the API call
        mock_client_instance.post.assert_called_once()
        call_args = mock_client_instance.post.call_args
        assert call_args[0][0] == "/v1/audio/speech"
        payload = call_args[1]["json"]
        assert payload["input"] == "Hello world"
        assert payload["voice"] == "test_voice"
        assert payload["language"] == "en"
        assert payload["exaggeration"] == 0.8

    @pytest.mark.asyncio
    async def test_generate_speech_from_chunks(self, tts_service, mock_httpx_client):
        """Test generating speech with automatic chunking."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake_audio_data"

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        tts_service.client = mock_client_instance

        # Text that will be split into multiple chunks
        text = ". ".join([f"Sentence {i}" for i in range(50)])

        results = await tts_service.generate_speech_from_chunks(text)

        # Should create multiple chunks
        assert len(results) > 1

        # Each result should be valid
        for i, result in enumerate(results):
            assert isinstance(result, TTSResult)
            assert result.chunk_index == i
            assert result.total_chunks == len(results)
            assert len(result.audio_data) > 0

    @pytest.mark.asyncio
    async def test_upload_voice_success(self, tts_service, tmp_path):
        """Test uploading a custom voice."""
        # Create a temporary voice file
        voice_file = tmp_path / "test_voice.wav"
        voice_file.write_bytes(b"fake_voice_data")

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        tts_service.client = mock_client_instance

        result = await tts_service.upload_voice(
            voice_file_path=voice_file,
            voice_name="my_voice",
            language="en",
        )

        assert result is True
        mock_client_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using TTS service as async context manager."""
        async with ChatterboxTTSService() as service:
            assert service is not None
            assert service.client is not None


@pytest.mark.parametrize(
    "text,expected_chunks",
    [
        ("Short text", 1),
        ("A" * 50 + ". " + "B" * 60 + ".", 2),
    ],
)
def test_chunk_text_parametrized(tts_service, text, expected_chunks):
    """Parametrized test for text chunking."""
    chunks = tts_service.chunk_text(text)
    assert len(chunks) == expected_chunks


class TestTTSConfig:
    """Test cases for TTSConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TTSConfig()
        assert config.exaggeration == 0.8
        assert config.cfg_weight == 0.3
        assert config.temperature == 0.9
        assert config.voice is None
        assert config.language is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = TTSConfig(
            voice="custom_voice",
            language="fr",
            exaggeration=1.2,
            cfg_weight=0.5,
            temperature=1.0,
        )
        assert config.voice == "custom_voice"
        assert config.language == "fr"
        assert config.exaggeration == 1.2
        assert config.cfg_weight == 0.5
        assert config.temperature == 1.0


class TestTTSChunk:
    """Test cases for TTSChunk."""

    def test_chunk_creation(self):
        """Test creating a TTSChunk."""
        chunk = TTSChunk(
            text="Test text",
            index=0,
            total_chunks=3,
        )
        assert chunk.text == "Test text"
        assert chunk.index == 0
        assert chunk.total_chunks == 3


class TestTTSResult:
    """Test cases for TTSResult."""

    def test_result_creation(self):
        """Test creating a TTSResult."""
        result = TTSResult(
            audio_data=b"test_audio",
            format="wav",
            chunk_index=1,
            total_chunks=5,
            duration_seconds=3.5,
        )
        assert result.audio_data == b"test_audio"
        assert result.format == "wav"
        assert result.chunk_index == 1
        assert result.total_chunks == 5
        assert result.duration_seconds == 3.5

    def test_result_default_format(self):
        """Test default format value."""
        result = TTSResult(
            audio_data=b"test",
            chunk_index=0,
            total_chunks=1,
        )
        assert result.format == "wav"
