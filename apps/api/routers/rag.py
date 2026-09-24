import asyncio
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from pydantic import BaseModel
from apps.api.core.config import settings
from apps.api.rag import ARCHITECTURES
from apps.api.schemas.rag import AnswerResult

router = APIRouter(prefix="/rag", tags=["rag"])

class CompareRequest(BaseModel):
    query: str
    top_k: int = 6

@router.get("/architectures")
async def list_architectures():
    return [
        {
            "name": "Hybrid",
            "tagline": "Dense + BM25s with Reciprocal Rank Fusion",
            "description": "Combines dense semantic vector search with sparse BM25s inverted indexing. Balances conceptual recall with exact technical term precision.",
            "strengths": ["Strong baseline", "Vocabulary robust", "Low hallucination"],
            "tradeoffs": ["Context window saturation on 30+ page docs"],
            "retrieval_strategy": "HNSW (text-embedding-3-large) + BM25s (k1=1.5, b=0.75)"
        },
        {
            "name": "Hierarchical",
            "tagline": "Parent-Child AST Chunking",
            "description": "Indexes 256-token child chunks for precision semantic lookup, then retrieves the surrounding 2,048-token parent section for synthesis.",
            "strengths": ["Eliminates lost-in-middle decay", "Global section context", "High synthesis coherence"],
            "tradeoffs": ["Larger LLM context payload"],
            "retrieval_strategy": "256-tok child -> 2048-tok parent tree resolution"
        },
        {
            "name": "GraphRAG",
            "tagline": "Entity & Knowledge Graph Traversal",
            "description": "Extracts entities, methods, and datasets into a connected graph. Traverses community clusters to answer relational and multi-hop questions.",
            "strengths": ["Cross-paper synthesis", "Dataset/method comparisons", "Multi-hop discovery"],
            "tradeoffs": ["Entity extraction overhead"],
            "retrieval_strategy": "NetworkX entity community search + linked chunks"
        },
        {
            "name": "Agentic",
            "tagline": "Corrective RAG (CRAG) State Machine",
            "description": "Uses self-reflective grading nodes to evaluate retrieval sufficiency. Automatically transforms or rewrites queries when evidence is deficient.",
            "strengths": ["Self-correcting", "Adaptive filtering", "Transparent iteration logs"],
            "tradeoffs": ["Higher latency per iteration"],
            "retrieval_strategy": "Grade -> Rewrite -> Re-retrieve state machine"
        },
        {
            "name": "Adaptive",
            "tagline": "Query Difficulty Classification & Routing",
            "description": "Dynamically classifies query complexity (simple, moderate, complex) and routes to the most cost-effective retrieval pipeline.",
            "strengths": ["Optimal cost/latency trade-off", "Explainable routing rationale"],
            "tradeoffs": ["Routing classifier dependency"],
            "retrieval_strategy": "Heuristic classifier -> dynamic dispatch"
        }
    ]

@router.post("/corpora/{corpus_id}/compare", response_model=Dict[str, AnswerResult])
async def compare_architectures(corpus_id: str, payload: CompareRequest):
    config = {"top_k": payload.top_k, "model": settings.DEFAULT_CHAT_MODEL}

    # Concurrently execute all 5 RAG architectures
    names = list(ARCHITECTURES.keys())
    tasks = [ARCHITECTURES[name].run(payload.query, corpus_id, config) for name in names]
    results_list = await asyncio.gather(*tasks, return_exceptions=False)
    results = dict(zip(names, results_list))
    return results
