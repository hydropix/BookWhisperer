"""
Text Chunking Service - Split large texts into manageable chunks for LLM and TTS processing.

This service provides strategies for:
- LLM chunking: Preserves context with overlap, respects token limits
- TTS chunking: Splits by sentences for natural speech flow
"""

import logging
import re
from typing import List, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""
    max_chars: int
    overlap_chars: int = 100
    min_chunk_size: int = 100


class TextChunker:
    """Service for chunking text into manageable pieces."""

    def __init__(self):
        """Initialize the chunker."""
        # Sentence-ending patterns
        self.sentence_endings = re.compile(r'([.!?]+["\'"\)]?\s+)')
        # Paragraph breaks
        self.paragraph_breaks = re.compile(r'\n\s*\n')

    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Split by sentence-ending punctuation
        sentences = self.sentence_endings.split(text)

        # Recombine sentences with their punctuation
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punctuation = sentences[i + 1] if i + 1 < len(sentences) else ''
            combined = (sentence + punctuation).strip()
            if combined:
                result.append(combined)

        # Handle last sentence if it doesn't end with punctuation
        if len(sentences) % 2 == 1:
            last = sentences[-1].strip()
            if last:
                result.append(last)

        return result

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.

        Args:
            text: Input text

        Returns:
            List of paragraphs
        """
        paragraphs = self.paragraph_breaks.split(text)
        return [p.strip() for p in paragraphs if p.strip()]

    def chunk_for_llm(
        self,
        text: str,
        max_chars: int = 4000,
        overlap_chars: int = 200
    ) -> List[str]:
        """
        Chunk text for LLM processing with context overlap.

        Strategy:
        1. Try to split by paragraphs first
        2. If paragraphs are too large, split by sentences
        3. Add overlap between chunks for context preservation
        4. Ensure no chunk exceeds max_chars

        Args:
            text: Text to chunk
            max_chars: Maximum characters per chunk (~4000 for most LLMs)
            overlap_chars: Characters to overlap between chunks for context

        Returns:
            List of text chunks
        """
        if not text or len(text) <= max_chars:
            return [text] if text else []

        logger.info(f"Chunking text ({len(text)} chars) for LLM with max={max_chars}, overlap={overlap_chars}")

        chunks = []
        current_chunk = ""
        paragraphs = self._split_into_paragraphs(text)

        for para in paragraphs:
            # If paragraph itself is too large, split by sentences
            if len(para) > max_chars:
                sentences = self._split_into_sentences(para)

                for sentence in sentences:
                    # If single sentence is too large, force split
                    if len(sentence) > max_chars:
                        logger.warning(f"Sentence exceeds max_chars ({len(sentence)}), force splitting")
                        # Split into hard chunks
                        for i in range(0, len(sentence), max_chars - overlap_chars):
                            chunk = sentence[i:i + max_chars]
                            if chunk.strip():
                                chunks.append(chunk.strip())
                        continue

                    # Check if adding sentence would exceed limit
                    if len(current_chunk) + len(sentence) + 1 > max_chars:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            # Start new chunk with overlap from end of previous chunk
                            overlap_start = max(0, len(current_chunk) - overlap_chars)
                            current_chunk = current_chunk[overlap_start:] + " " + sentence
                        else:
                            current_chunk = sentence
                    else:
                        current_chunk += (" " if current_chunk else "") + sentence

            else:
                # Check if adding paragraph would exceed limit
                if len(current_chunk) + len(para) + 2 > max_chars:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        # Start new chunk with overlap
                        overlap_start = max(0, len(current_chunk) - overlap_chars)
                        current_chunk = current_chunk[overlap_start:] + "\n\n" + para
                    else:
                        current_chunk = para
                else:
                    current_chunk += ("\n\n" if current_chunk else "") + para

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"Created {len(chunks)} chunks for LLM processing")
        return chunks

    def chunk_for_tts(
        self,
        text: str,
        max_chars: int = 5000
    ) -> List[str]:
        """
        Chunk text for TTS processing.

        Strategy:
        1. Split by sentences for natural speech flow
        2. Group sentences up to max_chars
        3. No overlap needed for TTS
        4. Preserve natural pauses

        Args:
            text: Text to chunk
            max_chars: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if not text or len(text) <= max_chars:
            return [text] if text else []

        logger.info(f"Chunking text ({len(text)} chars) for TTS with max={max_chars}")

        chunks = []
        current_chunk = ""
        sentences = self._split_into_sentences(text)

        for sentence in sentences:
            # If single sentence exceeds max, force split
            if len(sentence) > max_chars:
                logger.warning(f"Sentence exceeds max_chars for TTS ({len(sentence)}), force splitting")
                # Save current chunk if exists
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                # Split long sentence into hard chunks
                for i in range(0, len(sentence), max_chars):
                    chunk = sentence[i:i + max_chars]
                    if chunk.strip():
                        chunks.append(chunk.strip())
                continue

            # Check if adding sentence would exceed limit
            if len(current_chunk) + len(sentence) + 1 > max_chars:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += (" " if current_chunk else "") + sentence

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        logger.info(f"Created {len(chunks)} chunks for TTS processing")
        return chunks

    def reassemble_chunks(self, chunks: List[str], remove_overlap: bool = False) -> str:
        """
        Reassemble chunks back into a single text.

        Args:
            chunks: List of text chunks to reassemble
            remove_overlap: Whether to attempt to remove overlapping sections

        Returns:
            Reassembled text
        """
        if not chunks:
            return ""

        if len(chunks) == 1:
            return chunks[0]

        if remove_overlap:
            # This is a simple approach - for production might need smarter overlap detection
            result = chunks[0]
            for chunk in chunks[1:]:
                # Try to find overlap
                overlap_found = False
                for overlap_len in range(min(200, len(result), len(chunk)), 10, -10):
                    end_segment = result[-overlap_len:].strip()
                    start_segment = chunk[:overlap_len].strip()
                    if end_segment == start_segment:
                        result += chunk[overlap_len:]
                        overlap_found = True
                        break
                if not overlap_found:
                    result += "\n" + chunk
            return result
        else:
            # Simple concatenation
            return "\n".join(chunks)


# Singleton instance
_chunker: TextChunker = None


def get_text_chunker() -> TextChunker:
    """
    Get or create the singleton text chunker.

    Returns:
        TextChunker instance
    """
    global _chunker
    if _chunker is None:
        _chunker = TextChunker()
    return _chunker
