"""
PDF Content Extraction
Handles both native text PDFs and scanned image PDFs
"""
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from pypdf import PdfReader
import re
from typing import Dict, List


class PDFProcessor:
    """Extract text and structure from PDF files"""

    def __init__(self):
        self.min_text_length = 50  # Minimum characters to consider text extraction successful

    def extract(self, file_path: str) -> Dict:
        """
        Main extraction method

        Returns:
        {
            'text': str,
            'pages': List[Dict],
            'total_pages': int,
            'estimated_time_minutes': int,
            'extraction_method': str  # 'native' or 'ocr'
        }
        """
        # Try native text extraction first
        result = self._extract_native_text(file_path)

        # If native text extraction failed, use OCR
        if len(result['text']) < self.min_text_length:
            result = self._extract_with_ocr(file_path)
            result['extraction_method'] = 'ocr'
        else:
            result['extraction_method'] = 'native'

        # Estimate study time (2 minutes per page on average)
        result['estimated_time_minutes'] = result['total_pages'] * 2

        return result

    def _extract_native_text(self, file_path: str) -> Dict:
        """Extract text from native PDF (not scanned)"""
        pages = []
        full_text = []

        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""

                # Clean text
                text = self._clean_text(text)

                pages.append({
                    'page_number': page_num,
                    'text': text,
                    'word_count': len(text.split())
                })

                full_text.append(text)

        return {
            'text': '\n\n'.join(full_text),
            'pages': pages,
            'total_pages': len(pages)
        }

    def _extract_with_ocr(self, file_path: str) -> Dict:
        """Extract text using OCR for scanned PDFs"""
        pages = []
        full_text = []

        # Convert PDF to images
        images = convert_from_path(file_path)

        for page_num, image in enumerate(images, start=1):
            # Run OCR
            text = pytesseract.image_to_string(image)

            # Clean text
            text = self._clean_text(text)

            pages.append({
                'page_number': page_num,
                'text': text,
                'word_count': len(text.split())
            })

            full_text.append(text)

        return {
            'text': '\n\n'.join(full_text),
            'pages': pages,
            'total_pages': len(pages)
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove page numbers (common patterns)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

        # Remove headers/footers (heuristic: single line at start/end)
        lines = text.split('\n')
        if len(lines) > 3:
            # Remove likely header/footer
            if len(lines[0]) < 100:
                lines = lines[1:]
            if len(lines[-1]) < 100:
                lines = lines[:-1]

        text = '\n'.join(lines)

        # Normalize spaces
        text = text.strip()

        return text

    def segment_by_structure(self, text: str) -> List[Dict]:
        """
        Segment text into logical sections

        Returns sections with:
        - type: 'heading', 'paragraph', 'list', 'formula'
        - content: text content
        - level: heading level (for headings)
        """
        sections = []
        lines = text.split('\n')

        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect headings (all caps, short, or ends with colon)
            if self._is_heading(line):
                if current_section:
                    sections.append(current_section)

                current_section = {
                    'type': 'heading',
                    'content': line,
                    'level': self._get_heading_level(line)
                }

            # Detect formulas (contains math symbols)
            elif self._is_formula(line):
                if current_section and current_section['type'] != 'formula':
                    sections.append(current_section)
                    current_section = None

                if not current_section:
                    current_section = {
                        'type': 'formula',
                        'content': line
                    }
                else:
                    current_section['content'] += '\n' + line

            # Detect lists (starts with bullet or number)
            elif self._is_list_item(line):
                if current_section and current_section['type'] != 'list':
                    sections.append(current_section)
                    current_section = None

                if not current_section:
                    current_section = {
                        'type': 'list',
                        'content': line
                    }
                else:
                    current_section['content'] += '\n' + line

            # Regular paragraph
            else:
                if current_section and current_section['type'] != 'paragraph':
                    sections.append(current_section)
                    current_section = None

                if not current_section:
                    current_section = {
                        'type': 'paragraph',
                        'content': line
                    }
                else:
                    current_section['content'] += ' ' + line

        # Add last section
        if current_section:
            sections.append(current_section)

        return sections

    def _is_heading(self, line: str) -> bool:
        """Detect if line is a heading"""
        # All caps
        if line.isupper() and len(line) < 100:
            return True

        # Ends with colon
        if line.endswith(':') and len(line) < 100:
            return True

        # Starts with chapter/section number
        if re.match(r'^(Chapter|\d+\.|\d+\))\s+', line, re.IGNORECASE):
            return True

        return False

    def _get_heading_level(self, line: str) -> int:
        """Determine heading level (1-3)"""
        if re.match(r'^(Chapter|CHAPTER)', line):
            return 1

        if line.isupper():
            return 2

        return 3

    def _is_formula(self, line: str) -> bool:
        """Detect if line contains mathematical formulas"""
        math_symbols = ['=', '+', '-', '*', '/', '∫', '∑', '√', '²', '³', 'π', '≤', '≥', '∞']
        return any(symbol in line for symbol in math_symbols) and len(line) < 200

    def _is_list_item(self, line: str) -> bool:
        """Detect if line is a list item"""
        # Bullet points
        if re.match(r'^[•●○▪▫-]\s+', line):
            return True

        # Numbered lists
        if re.match(r'^\d+[\.)]\s+', line):
            return True

        # Lettered lists
        if re.match(r'^[a-z][\.)]\s+', line, re.IGNORECASE):
            return True

        return False
