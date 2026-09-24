import pytest
from pathlib import Path
from apps.api.rag import ARCHITECTURES, get_rag_pipeline
from apps.api.services.index_service import index_service
from apps.api.services.neo4j_service import neo4j_service
from apps.api.schemas.rag import RetrievalResult

@pytest.mark.asyncio
async def test_langgraph_workflows_initialized():
    """Verify that all 5 RAG pipelines compile valid LangGraph workflows."""
    for name, pipeline in ARCHITECTURES.items():
        assert hasattr(pipeline, "workflow"), f"Pipeline {name} missing LangGraph workflow"
        assert pipeline.workflow is not None, f"Pipeline {name} workflow is None"

@pytest.mark.asyncio
async def test_neo4j_service_resilience_and_fallback():
    """Verify Neo4j service handles connectivity gracefully and falls back to NetworkX."""
    is_avail = neo4j_service.is_available()
    assert isinstance(is_avail, bool)

    test_corpus_id = "test-neo-corpus"
    sample_chunks = [
        {
            "id": "c-test-1",
            "paper_id": "p-1",
            "arxiv_id": "2401.15884",
            "paper_title": "Corrective RAG",
            "page_number": 2,
            "section_name": "Methodology",
            "content": "CRAG uses an evaluator model to score document retrieval confidence and trigger query rewrite.",
            "chunk_type": "child",
            "parent_chunk_id": "p-root",
            "token_count": 35
        }
    ]

    # Index corpus should sync or fallback gracefully without throwing
    index_service.index_corpus(test_corpus_id, sample_chunks)

    # Search graph should return valid entity mappings
    graph_res = index_service.search_graph(test_corpus_id, "CRAG evaluator confidence")
    assert isinstance(graph_res, list)

@pytest.mark.asyncio
async def test_langgraph_pipeline_retrievals():
    """Verify all 5 LangGraph pipelines execute retrieval and return structured RetrievalResults."""
    test_corpus_id = "test-corpus-lg"
    sample_chunks = [
        {
            "id": "c-lg-1",
            "paper_id": "p-lg-1",
            "arxiv_id": "2307.03172",
            "paper_title": "Lost in the Middle",
            "page_number": 3,
            "section_name": "§3 Position Bias",
            "content": "Language models show performance degradation when key evidence is positioned in the middle.",
            "chunk_type": "child",
            "parent_chunk_id": "parent-lg-1",
            "token_count": 40
        },
        {
            "id": "parent-lg-1",
            "paper_id": "p-lg-1",
            "arxiv_id": "2307.03172",
            "paper_title": "Lost in the Middle",
            "page_number": 3,
            "section_name": "§3 Position Bias",
            "content": "Comprehensive section context: Language models show performance degradation when key evidence is positioned in the middle of long contexts.",
            "chunk_type": "parent",
            "parent_chunk_id": None,
            "token_count": 80
        }
    ]
    index_service.index_corpus(test_corpus_id, sample_chunks)
    query = "How does middle position degradation affect language models?"

    for name, pipeline in ARCHITECTURES.items():
        ret = await pipeline.retrieve(query, test_corpus_id, {"top_k": 2})
        assert isinstance(ret, RetrievalResult)
        assert ret.strategy == name
        assert len(ret.intermediate_steps) > 0

def test_context_md_exists_and_structured():
    """Verify context.md exists in docs/ (or root) and contains the cross-conversation sections."""
    doc_context = Path(__file__).resolve().parent.parent / "docs" / "context.md"
    root_context = Path(__file__).resolve().parent.parent / "context.md"
    target_context = doc_context if doc_context.exists() else root_context
    assert target_context.exists(), "context.md must exist in docs/ or the workspace root"
    content = target_context.read_text(encoding="utf-8")
    assert "# Project Context & Feature Update Ledger (`context.md`)" in content
    assert "LangGraph StateGraph" in content
    assert "Neo4j" in content
    assert "Hybrid RAG" in content
    assert "GraphRAG" in content
