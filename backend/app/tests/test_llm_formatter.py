"""
Tests for LLM Formatter Service

These tests verify:
- Ollama connection and health check
- Text formatting functionality
- Chunking and reassembly
- Error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.llm_formatter import LLMFormatterService, get_llm_formatter


class TestLLMFormatterService:
    """Test suite for LLM Formatter Service."""

    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client."""
        with patch('app.services.llm_formatter.ollama.Client') as mock_client:
            yield mock_client

    @pytest.fixture
    def formatter_service(self, mock_ollama_client):
        """Create a formatter service with mocked Ollama client."""
        service = LLMFormatterService()
        return service

    def test_build_format_prompt(self, formatter_service):
        """Test prompt building for text formatting."""
        text = "This is a test text with some typos and poor punctuation"
        prompt = formatter_service._build_format_prompt(text)

        assert text in prompt
        assert "format" in prompt.lower()
        assert "audiobook" in prompt.lower()
        assert "dialogue" in prompt.lower()

    def test_format_text_empty_input(self, formatter_service):
        """Test formatting with empty input returns empty string."""
        assert formatter_service.format_text("") == ""
        assert formatter_service.format_text("   ") == "   "

    @patch('app.services.llm_formatter.ollama.Client')
    def test_format_text_success(self, mock_client_class):
        """Test successful text formatting."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.generate.return_value = {
            'response': 'This is the formatted text with proper punctuation.'
        }
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        input_text = "this is unformatted text"
        result = service.format_text(input_text)

        # Verify
        assert result == "This is the formatted text with proper punctuation."
        mock_client.generate.assert_called_once()

        # Check generate call arguments
        call_args = mock_client.generate.call_args
        assert call_args[1]['model'] == service.model
        assert 'prompt' in call_args[1]
        assert input_text in call_args[1]['prompt']

    @patch('app.services.llm_formatter.ollama.Client')
    def test_format_text_with_temperature(self, mock_client_class):
        """Test formatting with custom temperature."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.generate.return_value = {
            'response': 'Formatted text'
        }
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        service.format_text("test", temperature=0.7)

        # Verify temperature was passed
        call_args = mock_client.generate.call_args
        assert call_args[1]['options']['temperature'] == 0.7

    @patch('app.services.llm_formatter.ollama.Client')
    def test_format_text_error_handling(self, mock_client_class):
        """Test error handling when Ollama fails."""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_client.generate.side_effect = Exception("Ollama connection failed")
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()

        with pytest.raises(Exception) as exc_info:
            service.format_text("test text")

        assert "Ollama connection failed" in str(exc_info.value)

    @patch('app.services.llm_formatter.ollama.Client')
    def test_format_text_chunks(self, mock_client_class):
        """Test formatting multiple text chunks."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            {'response': 'Formatted chunk 1'},
            {'response': 'Formatted chunk 2'},
            {'response': 'Formatted chunk 3'}
        ]
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        chunks = ["chunk 1", "chunk 2", "chunk 3"]
        results = service.format_text_chunks(chunks)

        # Verify
        assert len(results) == 3
        assert results[0] == "Formatted chunk 1"
        assert results[1] == "Formatted chunk 2"
        assert results[2] == "Formatted chunk 3"
        assert mock_client.generate.call_count == 3

    @patch('app.services.llm_formatter.ollama.Client')
    def test_check_health_success(self, mock_client_class):
        """Test health check when Ollama is available."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.list.return_value = {
            'models': [
                {'name': 'llama2'},
                {'name': 'mistral'}
            ]
        }
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        service.model = 'llama2'
        result = service.check_health()

        assert result is True
        mock_client.list.assert_called_once()

    @patch('app.services.llm_formatter.ollama.Client')
    def test_check_health_model_not_found(self, mock_client_class):
        """Test health check when configured model is not available."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.list.return_value = {
            'models': [
                {'name': 'mistral'}
            ]
        }
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        service.model = 'llama2'
        result = service.check_health()

        assert result is False

    @patch('app.services.llm_formatter.ollama.Client')
    def test_check_health_no_models(self, mock_client_class):
        """Test health check when no models are available."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.list.return_value = {'models': []}
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        result = service.check_health()

        assert result is False

    @patch('app.services.llm_formatter.ollama.Client')
    def test_check_health_connection_error(self, mock_client_class):
        """Test health check when connection fails."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.list.side_effect = Exception("Connection refused")
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        result = service.check_health()

        assert result is False

    @patch('app.services.llm_formatter.ollama.Client')
    def test_pull_model_success(self, mock_client_class):
        """Test successful model pulling."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.pull.return_value = None
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        service.model = 'llama2'
        result = service.pull_model()

        assert result is True
        mock_client.pull.assert_called_once_with('llama2')

    @patch('app.services.llm_formatter.ollama.Client')
    def test_pull_model_failure(self, mock_client_class):
        """Test model pulling failure."""
        # Setup mock
        mock_client = MagicMock()
        mock_client.pull.side_effect = Exception("Pull failed")
        mock_client_class.return_value = mock_client

        # Create service and test
        service = LLMFormatterService()
        result = service.pull_model()

        assert result is False

    def test_get_llm_formatter_singleton(self):
        """Test that get_llm_formatter returns singleton instance."""
        formatter1 = get_llm_formatter()
        formatter2 = get_llm_formatter()

        assert formatter1 is formatter2
        assert isinstance(formatter1, LLMFormatterService)
