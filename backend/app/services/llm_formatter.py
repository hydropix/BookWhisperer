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

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the audiobook formatter.

        Returns:
            System prompt string
        """
        return """You are a professional audiobook text formatter. Your goal is to prepare text for expressive TTS (Text-to-Speech) narration using Chatterbox TTS.

## Your tasks:

1. **Fix broken lines from poor EPUB conversion**: Remove spurious line breaks that split sentences or words incorrectly. Rejoin text that should flow continuously.
2. **Clean the text**: Fix typos, normalize punctuation, remove HTML tags and artifacts
3. **Improve readability**: Ensure proper sentence structure and grammar
4. **Format dialogue**: Use proper quotation marks and dialogue attribution
5. **Add natural pauses**: Use punctuation (commas, periods, ellipses) for pacing

## Fixing broken EPUB text (CRITICAL):

Poor quality EPUB files often have random line breaks in the middle of sentences. You MUST fix these.

Example of broken text:
```
une nuit »), l'adoubement instantané de Bielinski, l'étude de la
Déclaration des droits de l'homme
, l'abolition désirée du servage, le thé fort l'auront donc conduit devant ce peloton d'exécution qui ne tirera pas,
in extremis
```

Should become:
```
une nuit »), l'adoubement instantané de Bielinski, l'étude de la Déclaration des droits de l'homme, l'abolition désirée du servage, le thé fort l'auront donc conduit devant ce peloton d'exécution qui ne tirera pas, in extremis
```

Rules for fixing line breaks:
- If a line ends without sentence-ending punctuation (. ! ? :) and the next line continues the sentence, JOIN them
- Preserve intentional paragraph breaks (empty lines between paragraphs)
- Preserve line breaks after complete sentences
- Remove trailing spaces before line breaks

## Paralinguistic tags for emotions:

Chatterbox TTS supports special tags to add expressiveness. Insert these tags ONLY where genuinely appropriate based on the story context:

- [laugh] - When a character laughs or something is genuinely funny
- [chuckle] - For a soft, quiet laugh or amusement
- [cough] - When a character coughs
- [sigh] - When a character sighs (add this tag, it conveys emotion well)
- [gasp] - For moments of shock or surprise

### Examples of proper tag usage:
- Original: "Ha ha, that's hilarious!" she said.
- Formatted: [laugh] "That's hilarious!" she said.

- Original: He let out a long breath. "I'm exhausted."
- Formatted: [sigh] "I'm exhausted."

- Original: "What?!" She couldn't believe it.
- Formatted: [gasp] "What?!" She couldn't believe it.

## Formatting for expressive reading:

- Use "..." (ellipsis) for dramatic pauses or trailing off
- Use "—" (em dash) for abrupt interruptions
- Use ALL CAPS sparingly for shouted words
- Keep exclamation marks for emphasis

## STRICT RULES:
- Do NOT add content that wasn't in the original
- Do NOT remove any story content
- Do NOT add narrator commentary or stage directions
- Do NOT overuse paralinguistic tags (only where clearly appropriate)
- Output ONLY the formatted text, no explanations or meta-commentary"""

    def _build_user_message(self, text: str) -> str:
        """
        Build the user message containing the text to format.

        Args:
            text: Raw text to format

        Returns:
            User message string
        """
        return f"""Format the following text for audiobook narration. Output ONLY the formatted text, nothing else.

Text to format:
{text}"""

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

        system_prompt = self._get_system_prompt()
        user_message = self._build_user_message(text)

        try:
            logger.info(f"Formatting text chunk ({len(text)} chars) with model {self.model}")

            # Use chat API with system/user message separation
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': self.max_tokens,
                }
            )

            formatted_text = response['message']['content'].strip()

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
