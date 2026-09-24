import hashlib
import uuid
import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from apps.api.services.pdf_processor import ExtractedPage

try:
    import tiktoken
    tokenizer = tiktoken.get_encoding("cl100k_base")
except Exception:
    tokenizer = None

try:
    import fitz
except ImportError:
    fitz = None

SECTION_HEADER_RE = re.compile(
    r"^(?:(?:\d+(?:\.\d+)*|[IVXLCDM]+)\.?\s+)?(Abstract|Introduction|Background|Related Work|Architecture|Model Architecture|Model|Attention|Method|Methods|Methodology|Training|Experiments|Experimental Setup|Results|Analysis|Discussion|Limitations|Conclusion|Conclusions|References|Appendix)\b",
    re.IGNORECASE
)
NUMBER_ONLY_RE = re.compile(r"^(?:\d+(?:\.\d+)*|[IVXLCDM]+)\.?$")

class ChunkData:
    def __init__(
        self,
        id: str,
        content: str,
        page_number: int,
        section_name: str,
        chunk_type: str = "child",
        parent_chunk_id: Optional[str] = None,
        token_count: int = 0,
        text_hash: str = ""
    ):
        self.id = id
        self.content = content
        self.page_number = page_number
        self.section_name = section_name
        self.chunk_type = chunk_type
        self.parent_chunk_id = parent_chunk_id
        self.token_count = token_count
        self.text_hash = text_hash

class ChunkingService:
    @staticmethod
    def count_tokens(text: str) -> int:
        if tokenizer:
            try:
                return len(tokenizer.encode(text))
            except Exception:
                pass
        return len(text.split())

    @staticmethod
    def compute_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        raw = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in raw if s.strip()]

    def extract_sections_from_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts structural sections and paragraphs from an academic PDF using PyMuPDF blocks.
        Respects multi-column reading order and two-line header formats (e.g. ['3.2', 'Attention']).
        """
        sections: List[Dict[str, Any]] = []
        if not fitz or not pdf_path.exists():
            return sections

        try:
            doc = fitz.open(str(pdf_path))
            current_sec_title = "Abstract"
            current_sec_paras: List[Tuple[int, str]] = []
            current_page = 1

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1
                blocks = page.get_text("blocks")

                for b in blocks:
                    if b[6] != 0:  # Skip image blocks
                        continue
                    text = b[4].strip()
                    if not text:
                        continue

                    lines = [l.strip() for l in text.splitlines() if l.strip()]
                    if not lines:
                        continue

                    # Filter out isolated page numbers and arXiv timestamp banners
                    if len(lines) == 1 and (lines[0].isdigit() or re.match(r"^arXiv:\d+\.\d+", lines[0])):
                        continue

                    is_header = False
                    detected_title = ""

                    # Check multi-line header (e.g. ['3.2', 'Attention'])
                    if len(lines) <= 3 and NUMBER_ONLY_RE.match(lines[0]) and len(lines) > 1 and len(lines[1]) < 60:
                        is_header = True
                        detected_title = f"§{lines[0]} {lines[1]}"
                    elif len(lines[0]) < 70 and SECTION_HEADER_RE.match(lines[0]):
                        is_header = True
                        detected_title = lines[0]

                    if is_header:
                        if current_sec_paras:
                            sections.append({
                                "section_name": current_sec_title,
                                "page_number": current_page,
                                "paragraphs": current_sec_paras
                            })
                            current_sec_paras = []
                        current_sec_title = detected_title
                        current_page = page_num

                        # If remaining lines in same block belong to body paragraph
                        if len(lines) > 1 and not NUMBER_ONLY_RE.match(lines[0]):
                            text_rest = " ".join(lines[1:]).strip()
                            if text_rest:
                                current_sec_paras.append((page_num, text_rest))
                    else:
                        clean_para = " ".join(lines)
                        if len(clean_para) > 15:
                            current_sec_paras.append((page_num, clean_para))

            if current_sec_paras:
                sections.append({
                    "section_name": current_sec_title,
                    "page_number": current_page,
                    "paragraphs": current_sec_paras
                })
            doc.close()
        except Exception as e:
            print(f"[ChunkingService] Error reading PDF blocks {pdf_path}: {e}")

        return sections

    def extract_sections_from_pages(self, pages: List[ExtractedPage]) -> List[Dict[str, Any]]:
        """
        Fallback section extractor for extracted page text.
        Splits by paragraph boundaries and detected academic headers.
        """
        sections: List[Dict[str, Any]] = []
        current_sec_title = "Abstract / Introduction"
        current_sec_paras: List[Tuple[int, str]] = []
        current_page = 1

        for page in pages:
            page_num = page.page_number
            raw_text = page.text
            if not raw_text or len(raw_text.strip()) < 20:
                continue

            # Split into natural paragraphs
            paragraphs = [p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n", raw_text) if p.strip()]

            for para in paragraphs:
                first_line = para.split(". ")[0].strip()
                if len(first_line) < 70 and SECTION_HEADER_RE.match(first_line):
                    if current_sec_paras:
                        sections.append({
                            "section_name": current_sec_title,
                            "page_number": current_page,
                            "paragraphs": current_sec_paras
                        })
                        current_sec_paras = []
                    current_sec_title = first_line
                    current_page = page_num
                    rest = para[len(first_line):].strip()
                    if rest:
                        current_sec_paras.append((page_num, rest))
                else:
                    current_sec_paras.append((page_num, para))

        if current_sec_paras:
            sections.append({
                "section_name": current_sec_title,
                "page_number": current_page,
                "paragraphs": current_sec_paras
            })

        return sections

    def create_paper_structural_chunks(
        self,
        pdf_path: Optional[Path] = None,
        pages: Optional[List[ExtractedPage]] = None,
        target_child_tokens: int = 260
    ) -> List[ChunkData]:
        """
        Extracts structural, paper-grounded chunks according to actual academic paper sections and paragraphs.
        - Parent Chunks: Spans the complete logical section/subsection (e.g. §3.2 Attention, Abstract).
        - Child Chunks: Coherent semantic paragraphs within that section (never cuts sentences in half).
        """
        sections = []
        if pdf_path and pdf_path.exists() and fitz:
            sections = self.extract_sections_from_pdf(pdf_path)

        if not sections and pages:
            sections = self.extract_sections_from_pages(pages)

        if not sections:
            return []

        all_chunks: List[ChunkData] = []

        for sec in sections:
            sec_title = sec["section_name"]
            paras = sec["paragraphs"]
            if not paras:
                continue

            full_section_text = "\n\n".join([p[1] for p in paras])
            parent_id = str(uuid.uuid4())
            parent_tokens = self.count_tokens(full_section_text)
            first_page = sec["page_number"]

            # 1. Create Parent Chunk for the entire logical section
            parent_chunk = ChunkData(
                id=parent_id,
                content=full_section_text,
                page_number=first_page,
                section_name=sec_title,
                chunk_type="parent",
                parent_chunk_id=None,
                token_count=parent_tokens,
                text_hash=self.compute_hash(full_section_text)
            )
            all_chunks.append(parent_chunk)

            # 2. Build coherent, paragraph-grounded Child Chunks
            current_child_text: List[str] = []
            current_child_tokens = 0
            current_child_page = first_page

            for page_num, p_text in paras:
                p_tokens = self.count_tokens(p_text)

                # If an academic paragraph is very long, partition cleanly along complete sentence boundaries
                if p_tokens > 350:
                    sentences = self.split_into_sentences(p_text)
                    sub_group: List[str] = []
                    sub_tokens = 0

                    for s in sentences:
                        stok = self.count_tokens(s)
                        if sub_tokens + stok > target_child_tokens and sub_group:
                            child_content = f"[{sec_title}] " + " ".join(sub_group)
                            all_chunks.append(
                                ChunkData(
                                    id=str(uuid.uuid4()),
                                    content=child_content,
                                    page_number=page_num,
                                    section_name=sec_title,
                                    chunk_type="child",
                                    parent_chunk_id=parent_id,
                                    token_count=self.count_tokens(child_content),
                                    text_hash=self.compute_hash(child_content)
                                )
                            )
                            sub_group = [s]
                            sub_tokens = stok
                        else:
                            sub_group.append(s)
                            sub_tokens += stok

                    if sub_group:
                        child_content = f"[{sec_title}] " + " ".join(sub_group)
                        all_chunks.append(
                            ChunkData(
                                id=str(uuid.uuid4()),
                                content=child_content,
                                page_number=page_num,
                                section_name=sec_title,
                                chunk_type="child",
                                parent_chunk_id=parent_id,
                                token_count=self.count_tokens(child_content),
                                text_hash=self.compute_hash(child_content)
                            )
                        )
                else:
                    # Merge short consecutive paragraphs within the same section to create a coherent retrieval unit (~200-300 tokens)
                    if current_child_tokens + p_tokens > target_child_tokens and current_child_text:
                        child_content = f"[{sec_title}] " + " ".join(current_child_text)
                        all_chunks.append(
                            ChunkData(
                                id=str(uuid.uuid4()),
                                content=child_content,
                                page_number=current_child_page,
                                section_name=sec_title,
                                chunk_type="child",
                                parent_chunk_id=parent_id,
                                token_count=self.count_tokens(child_content),
                                text_hash=self.compute_hash(child_content)
                            )
                        )
                        current_child_text = [p_text]
                        current_child_tokens = p_tokens
                        current_child_page = page_num
                    else:
                        current_child_text.append(p_text)
                        current_child_tokens += p_tokens
                        current_child_page = page_num

            # Flush remaining paragraphs in this section
            if current_child_text:
                child_content = f"[{sec_title}] " + " ".join(current_child_text)
                all_chunks.append(
                    ChunkData(
                        id=str(uuid.uuid4()),
                        content=child_content,
                        page_number=current_child_page,
                        section_name=sec_title,
                        chunk_type="child",
                        parent_chunk_id=parent_id,
                        token_count=self.count_tokens(child_content),
                        text_hash=self.compute_hash(child_content)
                    )
                )

        return all_chunks

    def create_hierarchical_chunks(
        self,
        pages: List[ExtractedPage],
        target_child_tokens: int = 256,
        child_overlap_tokens: int = 40,
        target_parent_tokens: int = 2048,
        pdf_path: Optional[Path] = None
    ) -> List[ChunkData]:
        """
        Backwards-compatible gateway delegating to paper structural chunking.
        """
        return self.create_paper_structural_chunks(
            pdf_path=pdf_path,
            pages=pages,
            target_child_tokens=target_child_tokens
        )

chunking_service = ChunkingService()
