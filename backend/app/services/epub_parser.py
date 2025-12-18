"""
EPUB Parser Service

Handles parsing of EPUB files and extraction of chapters.
Uses ebooklib to read EPUB files and BeautifulSoup to extract text from HTML.
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ChapterData:
    """Data class for extracted chapter information"""
    def __init__(self, chapter_number: int, title: str, content: str):
        self.chapter_number = chapter_number
        self.title = title
        self.content = content
        self.word_count = len(content.split())
        self.character_count = len(content)


class EPUBParser:
    """Service for parsing EPUB files"""

    def __init__(self):
        self.book = None

    def parse_file(self, file_path: str) -> Dict:
        """
        Parse an EPUB file and extract metadata and chapters.

        Args:
            file_path: Path to the EPUB file

        Returns:
            Dict containing book metadata and chapters

        Raises:
            ValueError: If file is not a valid EPUB
            FileNotFoundError: If file doesn't exist
        """
        logger.info(f"Starting EPUB parsing: {file_path}")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"EPUB file not found: {file_path}")

        try:
            self.book = epub.read_epub(file_path)
        except Exception as e:
            logger.error(f"Failed to read EPUB file: {e}")
            raise ValueError(f"Invalid EPUB file: {e}")

        metadata = self._extract_metadata()
        chapters = self._extract_chapters()

        logger.info(f"Successfully parsed EPUB: {len(chapters)} chapters found")

        return {
            "metadata": metadata,
            "chapters": chapters,
            "total_chapters": len(chapters)
        }

    def _extract_metadata(self) -> Dict:
        """Extract metadata from EPUB file"""
        try:
            title = self.book.get_metadata('DC', 'title')
            title = title[0][0] if title else "Unknown Title"

            author = self.book.get_metadata('DC', 'creator')
            author = author[0][0] if author else "Unknown Author"

            language = self.book.get_metadata('DC', 'language')
            language = language[0][0] if language else "en"

            publisher = self.book.get_metadata('DC', 'publisher')
            publisher = publisher[0][0] if publisher else None

            return {
                "title": title,
                "author": author,
                "language": language,
                "publisher": publisher
            }
        except Exception as e:
            logger.warning(f"Error extracting metadata: {e}")
            return {
                "title": "Unknown Title",
                "author": "Unknown Author",
                "language": "en",
                "publisher": None
            }

    def _extract_chapters(self) -> List[ChapterData]:
        """
        Extract chapters from EPUB file.
        Uses the table of contents (spine) to identify chapters.
        """
        chapters = []
        chapter_number = 1

        # Get all document items from the book
        items = list(self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        logger.info(f"Found {len(items)} document items in EPUB")

        for item in items:
            try:
                # Extract HTML content
                content_html = item.get_content()

                # Parse HTML to extract text
                soup = BeautifulSoup(content_html, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                text = soup.get_text(separator='\n', strip=True)

                # Skip empty or very short chapters (likely not actual content)
                if len(text.strip()) < 100:
                    logger.debug(f"Skipping short content: {len(text)} chars")
                    continue

                # Try to extract chapter title from item
                title = self._extract_chapter_title(soup, item, chapter_number)

                # Clean up the text
                text = self._clean_text(text)

                chapter_data = ChapterData(
                    chapter_number=chapter_number,
                    title=title,
                    content=text
                )

                chapters.append(chapter_data)
                logger.debug(f"Extracted chapter {chapter_number}: {title} ({len(text)} chars)")

                chapter_number += 1

            except Exception as e:
                logger.error(f"Error processing chapter {chapter_number}: {e}")
                continue

        return chapters

    def _extract_chapter_title(self, soup: BeautifulSoup, item, chapter_number: int) -> str:
        """
        Extract chapter title from HTML content.
        Tries multiple strategies to find a meaningful title.
        """
        # Strategy 1: Look for h1, h2, h3 tags
        for tag in ['h1', 'h2', 'h3']:
            heading = soup.find(tag)
            if heading and heading.get_text(strip=True):
                return heading.get_text(strip=True)

        # Strategy 2: Look for title tag
        title_tag = soup.find('title')
        if title_tag and title_tag.get_text(strip=True):
            return title_tag.get_text(strip=True)

        # Strategy 3: Use item file name
        if hasattr(item, 'file_name') and item.file_name:
            # Clean up filename
            name = Path(item.file_name).stem
            name = name.replace('_', ' ').replace('-', ' ')
            if name and name.lower() != 'untitled':
                return name.title()

        # Strategy 4: Default to Chapter N
        return f"Chapter {chapter_number}"

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.
        Removes excessive whitespace and normalizes line breaks.
        """
        # Replace multiple newlines with double newline (paragraph separator)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        # Join with paragraph breaks
        text = '\n\n'.join(cleaned_lines)

        # Remove excessive spaces
        import re
        text = re.sub(r' +', ' ', text)

        return text


def parse_epub(file_path: str) -> Dict:
    """
    Convenience function to parse an EPUB file.

    Args:
        file_path: Path to the EPUB file

    Returns:
        Dict containing metadata and chapters
    """
    parser = EPUBParser()
    return parser.parse_file(file_path)
