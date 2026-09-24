import re
try:
    import pymupdf as fitz
except ImportError:
    import fitz
from pathlib import Path
from typing import List, Dict, Any

class ExtractedPage:
    def __init__(self, page_number: int, text: str, sections: List[Dict[str, Any]]):
        self.page_number = page_number
        self.text = text
        self.sections = sections

class PDFProcessor:
    # Broad multi-domain academic section detector (Math, Physics, Bio, CS, Engineering)
    SECTION_REGEX = re.compile(
        r"^(?:(?:\d+\.?\d*|[IVXLCDM]+\.?)\s+)?(Abstract|Introduction|Background|Related Work|Preliminary|Preliminaries|Model|Architecture|Methods?|Methodology|Experiments?|Experimental Setup|Results?|Analysis|Discussion|Limitations?|Conclusions?|References|Appendix|Proof|Theorems?)\b",
        re.IGNORECASE
    )

    def extract_document(self, pdf_path: Path) -> List[ExtractedPage]:
        pages: List[ExtractedPage] = []
        if not pdf_path.exists():
            return pages

        try:
            doc = fitz.open(str(pdf_path))
            current_section = "Abstract / Intro"

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1
                raw_text = page.get_text("text")

                # Clean text: normalize whitespace and remove non-printable characters
                clean_lines = []
                page_sections = []

                for line in raw_text.splitlines():
                    trimmed = line.strip()
                    if not trimmed:
                        continue

                    # Section detection heuristic: short line matching academic section headers
                    if len(trimmed) < 60 and self.SECTION_REGEX.match(trimmed):
                        current_section = trimmed
                        page_sections.append({"section": trimmed, "offset": len("\n".join(clean_lines))})

                    clean_lines.append(trimmed)

                full_text = "\n".join(clean_lines)

                pages.append(
                    ExtractedPage(
                        page_number=page_num,
                        text=full_text,
                        sections=page_sections or [{"section": current_section, "offset": 0}]
                    )
                )

            doc.close()
        except Exception as e:
            print(f"[PDFProcessor] Error reading {pdf_path}: {e}")

        return pages

pdf_processor = PDFProcessor()
