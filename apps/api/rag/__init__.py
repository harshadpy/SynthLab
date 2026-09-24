from typing import Dict
from apps.api.rag.base import RAGPipeline
from apps.api.rag.hybrid_rag import hybrid_rag
from apps.api.rag.hierarchical_rag import hierarchical_rag
from apps.api.rag.graph_rag import graph_rag
from apps.api.rag.agentic_rag import agentic_rag
from apps.api.rag.adaptive_rag import adaptive_rag

ARCHITECTURES: Dict[str, RAGPipeline] = {
    "Hybrid": hybrid_rag,
    "Hierarchical": hierarchical_rag,
    "GraphRAG": graph_rag,
    "Agentic": agentic_rag,
    "Adaptive": adaptive_rag
}

def get_rag_pipeline(strategy: str) -> RAGPipeline:
    return ARCHITECTURES.get(strategy, hybrid_rag)
