from typing import List, Optional
from pydantic import BaseModel

class ArXivPaperItem(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str] = []
    abstract: str
    categories: List[str] = []
    published_date: str
    pdf_url: str
    journal_ref: Optional[str] = None
    doi: Optional[str] = None

class ArXivSearchResponse(BaseModel):
    query: str
    total_results: int
    papers: List[ArXivPaperItem]
