import pytest
from apps.api.rag import ARCHITECTURES, get_rag_pipeline
from apps.api.services.index_service import index_service

@pytest.mark.asyncio
async def test_all_architectures_satisfy_protocol():
    test_corpus_id = "test-corpus-1"
    sample_chunks = [
        {
            "id": "c1",
            "paper_id": "p1",
            "arxiv_id": "2307.03172",
            "paper_title": "Lost in the Middle",
            "page_number": 4,
            "section_name": "§3.2 Positional Degradation",
            "content": "Retrieval performance in modern transformer models degrades significantly when relevant information resides in middle contexts.",
            "chunk_type": "child",
            "parent_chunk_id": "parent1",
            "token_count": 50
        }
    ]
    index_service.index_corpus(test_corpus_id, sample_chunks)

    query = "How does positional degradation affect retrieval?"

    for name, pipeline in ARCHITECTURES.items():
        ret = await pipeline.retrieve(query, test_corpus_id, {"top_k": 3})
        assert ret is not None
        assert ret.strategy == name

        ans = await pipeline.generate(query, ret, {"model": "gpt-4o"})
        assert ans is not None
        assert ans.strategy == name
        assert ans.latency_ms > 0
        assert ans.token_usage.get("total", 0) > 0
        assert len(ans.citations) > 0
        assert ans.citations[0].paper_title == "Lost in the Middle"
