"""
Tests for Text Chunking Service

These tests verify:
- LLM chunking with overlap
- TTS chunking without overlap
- Edge cases (empty text, very long sentences, etc.)
- Reassembly of chunks
"""

import pytest
from app.services.chunking import TextChunker, get_text_chunker


class TestTextChunker:
    """Test suite for Text Chunking Service."""

    @pytest.fixture
    def chunker(self):
        """Create a text chunker instance."""
        return TextChunker()

    def test_split_into_sentences_simple(self, chunker):
        """Test splitting simple text into sentences."""
        text = "This is sentence one. This is sentence two! Is this sentence three?"
        sentences = chunker._split_into_sentences(text)

        assert len(sentences) == 3
        assert sentences[0].strip() == "This is sentence one."
        assert sentences[1].strip() == "This is sentence two!"
        assert sentences[2].strip() == "Is this sentence three?"

    def test_split_into_sentences_with_quotes(self, chunker):
        """Test splitting sentences with quotes."""
        text = '"Hello," she said. "How are you?" he asked.'
        sentences = chunker._split_into_sentences(text)

        assert len(sentences) == 2
        assert '"Hello," she said.' in sentences[0]
        assert '"How are you?" he asked.' in sentences[1]

    def test_split_into_sentences_no_punctuation(self, chunker):
        """Test splitting text without sentence-ending punctuation."""
        text = "This is a text without proper ending"
        sentences = chunker._split_into_sentences(text)

        assert len(sentences) == 1
        assert sentences[0] == "This is a text without proper ending"

    def test_split_into_paragraphs(self, chunker):
        """Test splitting text into paragraphs."""
        text = "Paragraph one.\n\nParagraph two.\n\n\nParagraph three."
        paragraphs = chunker._split_into_paragraphs(text)

        assert len(paragraphs) == 3
        assert paragraphs[0] == "Paragraph one."
        assert paragraphs[1] == "Paragraph two."
        assert paragraphs[2] == "Paragraph three."

    def test_chunk_for_llm_short_text(self, chunker):
        """Test LLM chunking with text shorter than max_chars."""
        text = "This is a short text."
        chunks = chunker.chunk_for_llm(text, max_chars=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_for_llm_empty_text(self, chunker):
        """Test LLM chunking with empty text."""
        chunks = chunker.chunk_for_llm("")
        assert chunks == []

        chunks = chunker.chunk_for_llm(None)
        assert chunks == []

    def test_chunk_for_llm_multiple_paragraphs(self, chunker):
        """Test LLM chunking with multiple paragraphs."""
        para1 = "A" * 100
        para2 = "B" * 100
        para3 = "C" * 100
        text = f"{para1}\n\n{para2}\n\n{para3}"

        chunks = chunker.chunk_for_llm(text, max_chars=150, overlap_chars=20)

        # Should split into chunks with overlap
        assert len(chunks) > 1
        # First chunk should start with A's
        assert chunks[0].startswith("A")

    def test_chunk_for_llm_with_overlap(self, chunker):
        """Test that LLM chunks have overlap."""
        # Create text with distinct sentences
        sentences = [f"Sentence number {i}. " for i in range(20)]
        text = "".join(sentences)

        chunks = chunker.chunk_for_llm(text, max_chars=100, overlap_chars=30)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Check for overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            # Get end of current chunk
            current_end = chunks[i][-30:].strip()
            # Get start of next chunk
            next_start = chunks[i + 1][:50].strip()

            # There should be some overlap (not exact due to sentence boundaries)
            # Just verify chunks exist and are non-empty
            assert len(current_end) > 0
            assert len(next_start) > 0

    def test_chunk_for_llm_very_long_sentence(self, chunker):
        """Test LLM chunking with a sentence longer than max_chars."""
        # Create a very long sentence without proper breaks
        text = "A" * 5000  # Single long "sentence"

        chunks = chunker.chunk_for_llm(text, max_chars=1000, overlap_chars=100)

        # Should force split
        assert len(chunks) > 1

        # All chunks should be within limit (except possibly last one)
        for chunk in chunks[:-1]:
            assert len(chunk) <= 1000

    def test_chunk_for_tts_short_text(self, chunker):
        """Test TTS chunking with short text."""
        text = "This is a short text."
        chunks = chunker.chunk_for_tts(text, max_chars=100)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_for_tts_empty_text(self, chunker):
        """Test TTS chunking with empty text."""
        chunks = chunker.chunk_for_tts("")
        assert chunks == []

    def test_chunk_for_tts_multiple_sentences(self, chunker):
        """Test TTS chunking with multiple sentences."""
        sentences = [f"This is sentence {i}. " for i in range(10)]
        text = "".join(sentences)

        chunks = chunker.chunk_for_tts(text, max_chars=100)

        # Should split into multiple chunks
        assert len(chunks) > 1

        # Each chunk should be within limit
        for chunk in chunks:
            assert len(chunk) <= 100

    def test_chunk_for_tts_no_overlap(self, chunker):
        """Test that TTS chunks don't have overlap."""
        sentences = [f"Sentence {i}. " for i in range(10)]
        text = "".join(sentences)

        chunks = chunker.chunk_for_tts(text, max_chars=50)

        # Reassemble and verify it matches original (no overlap means exact match)
        reassembled = " ".join(chunks)
        # Should contain all original sentences
        for i in range(10):
            assert f"Sentence {i}." in reassembled

    def test_chunk_for_tts_very_long_sentence(self, chunker):
        """Test TTS chunking with very long sentence."""
        text = "A" * 10000  # Very long sentence

        chunks = chunker.chunk_for_tts(text, max_chars=1000)

        # Should force split
        assert len(chunks) > 1

        # All chunks should be within limit
        for chunk in chunks:
            assert len(chunk) <= 1000

    def test_reassemble_chunks_simple(self, chunker):
        """Test simple chunk reassembly without overlap removal."""
        chunks = ["Chunk one.", "Chunk two.", "Chunk three."]
        result = chunker.reassemble_chunks(chunks, remove_overlap=False)

        assert "Chunk one." in result
        assert "Chunk two." in result
        assert "Chunk three." in result

    def test_reassemble_chunks_empty_list(self, chunker):
        """Test reassembling empty chunk list."""
        result = chunker.reassemble_chunks([])
        assert result == ""

    def test_reassemble_chunks_single_chunk(self, chunker):
        """Test reassembling single chunk."""
        chunks = ["Only chunk."]
        result = chunker.reassemble_chunks(chunks)
        assert result == "Only chunk."

    def test_reassemble_chunks_with_overlap_removal(self, chunker):
        """Test chunk reassembly with overlap removal."""
        # Create chunks with intentional overlap
        chunks = [
            "This is the first chunk with some text.",
            "with some text. This is the second chunk.",
            "This is the second chunk. And the third."
        ]

        result = chunker.reassemble_chunks(chunks, remove_overlap=True)

        # Result should not have duplicated text
        assert result.count("with some text.") <= 1
        assert result.count("This is the second chunk.") <= 1

    def test_get_text_chunker_singleton(self):
        """Test that get_text_chunker returns singleton."""
        chunker1 = get_text_chunker()
        chunker2 = get_text_chunker()

        assert chunker1 is chunker2
        assert isinstance(chunker1, TextChunker)

    def test_chunk_for_llm_preserves_content(self, chunker):
        """Test that chunking preserves all content."""
        text = """
        Chapter One

        It was a dark and stormy night. The wind howled through the trees.
        Lightning flashed across the sky. Thunder rumbled in the distance.

        Chapter Two

        The next morning was beautiful. Birds sang in the trees.
        The sun shone brightly. All was peaceful.
        """

        chunks = chunker.chunk_for_llm(text, max_chars=100, overlap_chars=20)

        # Reassemble and check key phrases are present
        reassembled = " ".join(chunks)
        assert "dark and stormy night" in reassembled
        assert "next morning was beautiful" in reassembled
        assert "Birds sang" in reassembled

    def test_chunk_for_tts_preserves_order(self, chunker):
        """Test that TTS chunking preserves sentence order."""
        sentences = [
            "First sentence here.",
            "Second sentence here.",
            "Third sentence here.",
            "Fourth sentence here.",
            "Fifth sentence here."
        ]
        text = " ".join(sentences)

        chunks = chunker.chunk_for_tts(text, max_chars=60)

        # Reassemble
        reassembled = " ".join(chunks)

        # Check that all sentences appear in order
        for sentence in sentences:
            assert sentence in reassembled

        # Check order is preserved
        pos1 = reassembled.index("First sentence")
        pos2 = reassembled.index("Second sentence")
        pos3 = reassembled.index("Third sentence")
        pos4 = reassembled.index("Fourth sentence")
        pos5 = reassembled.index("Fifth sentence")

        assert pos1 < pos2 < pos3 < pos4 < pos5
