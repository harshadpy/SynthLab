import pytest
from apps.api.services.evaluation_service import evaluation_service
from apps.api.services.index_service import index_service

@pytest.mark.asyncio
async def test_evaluation_benchmark_execution():
    test_corpus_id = "test-eval-corpus"
    sample_chunks = [
        {
            "id": "c_eval_1",
            "paper_id": "p1",
            "arxiv_id": "2307.03172",
            "paper_title": "Lost in the Middle",
            "page_number": 4,
            "section_name": "§3.2 Positional Degradation",
            "content": "Retrieval performance in modern transformer models degrades significantly in middle positions.",
            "chunk_type": "child",
            "parent_chunk_id": "p_eval_1",
            "token_count": 60
        }
    ]
    index_service.index_corpus(test_corpus_id, sample_chunks)

    results = await evaluation_service.run_benchmark(test_corpus_id, ["Hybrid", "Hierarchical", "Adaptive"])
    assert results is not None
    assert "Hybrid" in results
    assert "Hierarchical" in results
    assert "Adaptive" in results

    hybrid_res = results["Hybrid"]
    assert hybrid_res["correctness"] > 0
    assert hybrid_res["faithfulness"] > 0
    assert hybrid_res["latency_ms"] > 0
    assert hybrid_res["tokens"] > 0
    assert "estimated_cost" in hybrid_res
