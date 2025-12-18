"""
TXT Parser Service

Handles parsing of plain text files and extraction of chapters.
Uses heuristics to detect chapter boundaries and encoding detection.
"""

import logging
import re
from typing import List, Dict, Optional
from pathlib import Path
import chardet

logger = logging.getLogger(__name__)


class ChapterData:
    """Data class for extracted chapter information"""
    def __init__(self, chapter_number: int, title: str, content: str):
        self.chapter_number = chapter_number
        self.title = title
        self.content = content
        self.word_count = len(content.split())
        self.character_count = len(content)


class TXTParser:
    """Service for parsing plain text files"""

    # Patterns for detecting chapter markers
    CHAPTER_PATTERNS = [
        # "Chapter 1", "Chapter One", "CHAPTER 1"
        r'^(?:CHAPTER|Chapter|chapter)\s+(?:\d+|[IVXivx]+|[A-Z][a-z]+)\s*[:\-.]?\s*(.*)$',
        # "1. Title", "I. Title"
        r'^(?:\d+|[IVXivx]+)\.\s+(.+)$',
        # "Part 1", "PART I"
        r'^(?:PART|Part|part)\s+(?:\d+|[IVXivx]+)\s*[:\-.]?\s*(.*)$',
        # Simple numbered chapters: "1", "2", etc (on their own line)
        r'^\s*(\d+)\s*$',
    ]

    def __init__(self):
        self.content = ""
        self.encoding = "utf-8"

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse a TXT file and extract chapters.

        Args:
            file_path: Path to the TXT file

        Returns:
            Dict containing book metadata and chapters

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file cannot be decoded
        """
        logger.info(f"Starting TXT parsing: {file_path}")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"TXT file not found: {file_path}")

        # Detect encoding and read file
        self._read_file(file_path)

        # Extract basic metadata
        metadata = self._extract_metadata(file_path)

        # Extract chapters using heuristics
        chapters = self._extract_chapters()

        logger.info(f"Successfully parsed TXT: {len(chapters)} chapters found")

        return {
            "metadata": metadata,
            "chapters": chapters,
            "total_chapters": len(chapters)
        }

    def _read_file(self, file_path: str):
        """Read file with encoding detection"""
        try:
            # First, detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                self.encoding = result['encoding'] or 'utf-8'
                confidence = result['confidence']

            logger.info(f"Detected encoding: {self.encoding} (confidence: {confidence:.2f})")

            # Read file with detected encoding
            with open(file_path, 'r', encoding=self.encoding, errors='replace') as f:
                self.content = f.read()

        except Exception as e:
            logger.error(f"Error reading file: {e}")
            # Fallback to UTF-8
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    self.content = f.read()
                    self.encoding = 'utf-8'
            except Exception as e2:
                raise ValueError(f"Failed to read file: {e2}")

    def _extract_metadata(self, file_path: str) -> Dict:
        """
        Extract basic metadata from TXT file.
        Limited compared to EPUB - uses filename and tries to detect title.
        """
        # Use filename as fallback title
        filename = Path(file_path).stem
        title = filename.replace('_', ' ').replace('-', ' ').title()

        # Try to extract title from first lines
        lines = self.content.split('\n')[:10]
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 100:
                # Could be a title
                if not any(pattern for pattern in self.CHAPTER_PATTERNS
                          if re.match(pattern, line, re.MULTILINE)):
                    title = line
                    break

        return {
            "title": title,
            "author": "Unknown Author",
            "language": "en",
            "encoding": self.encoding
        }

    def _extract_chapters(self) -> List[ChapterData]:
        """
        Extract chapters using pattern matching heuristics.
        """
        # Split content into lines for processing
        lines = self.content.split('\n')

        # Find chapter boundaries
        chapter_markers = self._find_chapter_markers(lines)

        if not chapter_markers:
            logger.warning("No chapter markers found, treating entire file as one chapter")
            # Treat entire file as single chapter
            return [ChapterData(
                chapter_number=1,
                title="Full Text",
                content=self._clean_text(self.content)
            )]

        # Extract chapters based on markers
        chapters = self._split_into_chapters(lines, chapter_markers)

        return chapters

    def _find_chapter_markers(self, lines: List[str]) -> List[Dict]:
        """
        Find lines that mark chapter boundaries.

        Returns:
            List of dicts with 'line_number', 'title', and 'pattern'
        """
        markers = []

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            if not line_stripped:
                continue

            # Try each pattern
            for pattern in self.CHAPTER_PATTERNS:
                match = re.match(pattern, line_stripped, re.MULTILINE)
                if match:
                    # Extract title if captured, otherwise use the line
                    title = match.group(1) if match.lastindex and match.lastindex >= 1 else line_stripped
                    title = title.strip()

                    if not title:
                        title = line_stripped

                    markers.append({
                        'line_number': i,
                        'title': title,
                        'pattern': pattern
                    })
                    logger.debug(f"Found chapter marker at line {i}: {title}")
                    break

        # Filter out false positives (markers too close together)
        if len(markers) > 1:
            markers = self._filter_markers(markers, lines)

        return markers

    def _filter_markers(self, markers: List[Dict], lines: List[str]) -> List[Dict]:
        """
        Filter out false positive chapter markers.
        Removes markers that are too close together (likely not real chapters).
        """
        MIN_LINES_BETWEEN_CHAPTERS = 50  # Minimum lines between chapters

        filtered = [markers[0]]  # Keep first marker

        for marker in markers[1:]:
            prev_marker = filtered[-1]
            lines_between = marker['line_number'] - prev_marker['line_number']

            if lines_between >= MIN_LINES_BETWEEN_CHAPTERS:
                filtered.append(marker)
            else:
                logger.debug(f"Filtering out marker at line {marker['line_number']} (too close to previous)")

        return filtered

    def _split_into_chapters(self, lines: List[str], markers: List[Dict]) -> List[ChapterData]:
        """
        Split content into chapters based on markers.
        """
        chapters = []

        for i, marker in enumerate(markers):
            start_line = marker['line_number']
            end_line = markers[i + 1]['line_number'] if i + 1 < len(markers) else len(lines)

            # Extract chapter content (skip the chapter title line itself)
            chapter_lines = lines[start_line + 1:end_line]
            chapter_content = '\n'.join(chapter_lines)

            # Clean the content
            chapter_content = self._clean_text(chapter_content)

            # Skip if content is too short (likely not a real chapter)
            if len(chapter_content.strip()) < 100:
                logger.warning(f"Skipping short chapter: {marker['title']}")
                continue

            chapter_data = ChapterData(
                chapter_number=len(chapters) + 1,
                title=marker['title'] or f"Chapter {len(chapters) + 1}",
                content=chapter_content
            )

            chapters.append(chapter_data)
            logger.debug(f"Extracted chapter {chapter_data.chapter_number}: "
                        f"{chapter_data.title} ({len(chapter_content)} chars)")

        return chapters

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        Removes excessive whitespace and normalizes formatting.
        """
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Remove trailing/leading whitespace from each line
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)

        # Remove excessive spaces
        text = re.sub(r' {2,}', ' ', text)

        # Trim
        text = text.strip()

        return text


def parse_txt(file_path: str) -> Dict:
    """
    Convenience function to parse a TXT file.

    Args:
        file_path: Path to the TXT file

    Returns:
        Dict containing metadata and chapters
    """
    parser = TXTParser()
    return parser.parse_file(file_path)
