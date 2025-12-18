"""
LLM Formatter Service - Uses Ollama to format and clean text for audiobook generation.

This service:
- Connects to local Ollama instance
- Formats text chunks using LLM (cleaning, punctuation, dialogue detection)
- Handles chunking for large texts that exceed model context limits
"""

import logging
from typing import Optional, List
import ollama
from app.config import settings

logger = logging.getLogger(__name__)


class LLMFormatterService:
    """Service for formatting text using Ollama LLM."""

    def __init__(self):
        """Initialize the LLM formatter with Ollama client."""
        self.client = ollama.Client(host=settings.OLLAMA_URL)
        self.model = settings.OLLAMA_MODEL
        self.max_tokens = settings.OLLAMA_MAX_TOKENS

    def _build_format_prompt(self, text: str) -> str:
        """
        Build a prompt for formatting text for audiobook narration.

        Args:
            text: Raw text to format

        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are a professional text formatter preparing content for audiobook narration.

Your task is to:
1. Clean and normalize the text (fix typos, normalize punctuation)
2. Ensure proper sentence structure and grammar
3. Identify dialogue and format it clearly
4. Add appropriate punctuation for natural pauses
5. Remove any formatting artifacts (HTML tags, special characters that won't be read)
6. Keep the meaning and content exactly the same - only improve formatting

IMPORTANT:
- Do NOT add content that wasn't in the original
- Do NOT remove story content
- Do NOT add narrator notes or stage directions
- Output ONLY the formatted text, no explanations

Text to format:
{text}

Formatted text:"""
        return prompt

    def format_text(self, text: str, temperature: float = 0.3) -> str:
        """
        Format a single chunk of text using the LLM.

        Args:
            text: Text chunk to format
            temperature: LLM temperature (lower = more deterministic)

        Returns:
            Formatted text

        Raises:
            Exception: If Ollama request fails
        """
        if not text or not text.strip():
            return text

        prompt = self._build_format_prompt(text)

        try:
            logger.info(f"Formatting text chunk ({len(text)} chars) with model {self.model}")

            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    'temperature': temperature,
                    'num_predict': self.max_tokens,
                }
            )

            formatted_text = response['response'].strip()
            logger.info(f"Successfully formatted chunk ({len(formatted_text)} chars)")

            return formatted_text

        except Exception as e:
            logger.error(f"Error formatting text with Ollama: {str(e)}")
            raise

    def format_text_chunks(
        self,
        chunks: List[str],
        temperature: float = 0.3
    ) -> List[str]:
        """
        Format multiple text chunks.

        Args:
            chunks: List of text chunks to format
            temperature: LLM temperature

        Returns:
            List of formatted text chunks

        Raises:
            Exception: If any chunk formatting fails
        """
        formatted_chunks = []

        for i, chunk in enumerate(chunks, 1):
            logger.info(f"Processing chunk {i}/{len(chunks)}")
            formatted = self.format_text(chunk, temperature)
            formatted_chunks.append(formatted)

        return formatted_chunks

    def check_health(self) -> bool:
        """
        Check if Ollama is available and the model is loaded.

        Returns:
            True if Ollama is healthy, False otherwise
        """
        try:
            # List available models
            models = self.client.list()

            # Check if our configured model is available
            model_names = [m['name'] for m in models.get('models', [])]

            if not model_names:
                logger.warning("No models found in Ollama")
                return False

            # Check if our specific model is available
            if self.model not in model_names:
                logger.warning(
                    f"Configured model '{self.model}' not found. "
                    f"Available models: {model_names}"
                )
                return False

            logger.info(f"Ollama health check passed. Model '{self.model}' is available.")
            return True

        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False

    def pull_model(self) -> bool:
        """
        Pull/download the configured model if not available.

        Returns:
            True if model was pulled successfully, False otherwise
        """
        try:
            logger.info(f"Pulling model '{self.model}' from Ollama...")
            self.client.pull(self.model)
            logger.info(f"Successfully pulled model '{self.model}'")
            return True

        except Exception as e:
            logger.error(f"Failed to pull model '{self.model}': {str(e)}")
            return False


# Singleton instance
_formatter_service: Optional[LLMFormatterService] = None


def get_llm_formatter() -> LLMFormatterService:
    """
    Get or create the singleton LLM formatter service.

    Returns:
        LLMFormatterService instance
    """
    global _formatter_service

    if _formatter_service is None:
        _formatter_service = LLMFormatterService()

    return _formatter_service
