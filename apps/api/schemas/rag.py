from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class Citation(BaseModel):
    chunk_id: str
    paper_id: str
    arxiv_id: str
    paper_title: str
    page_number: int
    section_name: Optional[str] = "Main Text"
    content: str
    similarity_score: float = 0.0
    bm25_score: float = 0.0
    reranker_score: Optional[float] = None
    rank: int = 1
    token_range: Optional[str] = None
    attention_depth: Optional[str] = "middle"  # start, middle, end
    strategy_metadata: Optional[Dict[str, Any]] = None

class RetrievalResult(BaseModel):
    query: str
    strategy: str
    citations: List[Citation]
    retrieval_latency_ms: int = 0
    intermediate_steps: List[Dict[str, Any]] = []

class AnswerResult(BaseModel):
    answer: str
    citations: List[Citation]
    strategy: str
    model: str
    latency_ms: int
    retrieval_latency_ms: int
    generation_latency_ms: int
    token_usage: Dict[str, int]
    trace_id: Optional[str] = None
    intermediate_steps: List[Dict[str, Any]] = []

class ChatQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    strategy: str = Field(default="Hybrid")  # Hybrid, Hierarchical, GraphRAG, Agentic, Adaptive
    scope: str = Field(default="Entire corpus")  # Entire corpus, This paper, Compare all
    paper_id: Optional[str] = None  # if scope is "This paper"
    top_k: int = 8
    reranker: Optional[str] = "Cohere-v3"
    conversation_id: Optional[str] = None

class FeedbackRequest(BaseModel):
    rating: str  # helpful, not_helpful, correct, incorrect, missing_evidence
    comment: Optional[str] = None
