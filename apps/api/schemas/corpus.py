from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class CorpusCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    query: Optional[str] = None
    paper_ids: List[str] = Field(default_factory=list)  # arXiv IDs to ingest

class CorpusUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PaperResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corpus_id: str
    arxiv_id: str
    title: str
    authors: List[str] = []
    abstract: Optional[str] = None
    categories: List[str] = []
    published_date: Optional[str] = None
    pdf_url: Optional[str] = None
    status: str
    status_message: Optional[str] = None
    page_count: int = 0
    chunk_count: int = 0
    created_at: datetime

class CorpusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    query: Optional[str] = None
    status: str
    paper_count: int = 0
    page_count: int = 0
    chunk_count: int = 0
    categories: List[str] = []
    created_at: datetime
    updated_at: datetime
    papers: List[PaperResponse] = []

