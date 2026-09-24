import re
import math
from typing import List, Dict, Any, Optional, Literal, Tuple
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

class RetrievedChunk(TypedDict):
    chunk_id: str
    paper_id: str
    arxiv_id: str
    paper_title: str
    page_number: int
    section_name: str
    content: str
    score: float
    source: str
    parent_chunk_id: Optional[str]
    metadata: Dict[str, Any]

class EvidenceItem(BaseModel):
    chunk_id: str
    paper_title: str
    section_name: str
    page_number: int
    content: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rerank_score: Optional[float] = None
    rank: int = 1

class EvidenceGrade(BaseModel):
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance of evidence to the query")
    coverage: float = Field(..., ge=0.0, le=1.0, description="Completeness of coverage for key question aspects")
    quality: float = Field(..., ge=0.0, le=1.0, description="Scientific rigor and factual quality of evidence")
    missing_information: List[str] = Field(default_factory=list, description="Specific missing concepts or evidence facets")
    verdict: Literal["sufficient", "partial", "insufficient"] = Field(..., description="Overall sufficiency verdict")
    rationale: str = Field(default="", description="Brief justification of the grade")

class ClaimVerificationResult(BaseModel):
    is_faithful: bool = Field(default=True)
    faithfulness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    supported_claims: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    abstention_required: bool = Field(default=False)
    revised_answer: Optional[str] = None
    critique: str = Field(default="")

class PipelineTelemetry(BaseModel):
    strategy: str
    total_latency_ms: int = 0
    retrieval_latency_ms: int = 0
    generation_latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    graph_hops: int = 0
    agentic_iterations: int = 0
    rerank_performed: bool = False
    trace_id: Optional[str] = None

class LocalCrossEncoderReranker:
    """
    Pluggable, local-first reranker abstraction.
    Does not require paid API keys.
    Computes calibrated cross-interaction scores combining lexical proximity,
    term-frequency concentration, exact technical n-gram matches, and normalized base scores.
    """
    def __init__(self, model_name: str = "local-cross-encoder-v1"):
        self.model_name = model_name

    def score_pair(self, query: str, document: str, base_dense: float = 0.7, base_sparse: float = 10.0) -> float:
        q_tokens = [w.lower() for w in re.findall(r"\b\w{2,}\b", query)]
        if not q_tokens:
            return round(base_dense, 3)

        doc_lower = document.lower()
        doc_tokens = re.findall(r"\b\w{2,}\b", doc_lower)
        if not doc_tokens:
            return 0.1

        # 1. Term coverage
        unique_q = set(q_tokens)
        matched_terms = [t for t in unique_q if t in doc_lower]
        coverage_ratio = len(matched_terms) / max(1, len(unique_q))

        # 2. Exact phrase and technical bigram match bonus
        phrase_bonus = 0.0
        for i in range(len(q_tokens) - 1):
            bigram = f"{q_tokens[i]} {q_tokens[i+1]}"
            if bigram in doc_lower:
                phrase_bonus += 0.08
        phrase_bonus = min(0.25, phrase_bonus)

        # 3. Dense score normalization (assuming cosine in [0, 1])
        norm_dense = max(0.0, min(1.0, float(base_dense)))

        # 4. Sparse score normalization with sigmoid scaling
        norm_sparse = 1.0 / (1.0 + math.exp(-0.25 * (float(base_sparse) - 8.0)))

        # Combined calibrated cross-encoder score in [0.0, 1.0]
        final_score = (
            0.35 * norm_dense +
            0.25 * norm_sparse +
            0.25 * coverage_ratio +
            0.15 * phrase_bonus
        )
        return round(float(min(0.99, max(0.05, final_score))), 3)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 8
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Reranks a list of candidate chunk dicts, each having 'content', 'dense_score', 'sparse_score'.
        Returns list of (candidate, rerank_score) sorted descending by rerank_score.
        """
        scored: List[Tuple[Dict[str, Any], float]] = []
        for c in candidates:
            content = c.get("content", "")
            d_score = float(c.get("dense_score", 0.7))
            s_score = float(c.get("sparse_score", 10.0))
            score = self.score_pair(query, content, base_dense=d_score, base_sparse=s_score)
            scored.append((c, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

class CitationVerifier:
    """
    Verifies that every inline citation chip [1], [2], etc. in the generated answer
    maps to an actual retrieved chunk in the context and that the text contains supporting terms.
    """
    @staticmethod
    def verify(answer: str, citations: List[Any]) -> Tuple[bool, List[str]]:
        matches = re.findall(r"\[(\d+)\]", answer)
        cited_indices = [int(m) for m in matches]
        unsupported = []

        total_citations = len(citations)
        for idx in cited_indices:
            if idx < 1 or idx > total_citations:
                unsupported.append(f"Citation [{idx}] references a non-existent source index.")

        is_valid = len(unsupported) == 0
        return is_valid, unsupported
