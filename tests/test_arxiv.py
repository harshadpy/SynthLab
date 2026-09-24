import pytest
from apps.api.services.arxiv_service import arxiv_service

@pytest.mark.asyncio
async def test_arxiv_search():
    res = await arxiv_service.search("transformer context degradation", max_results=5)
    assert res is not None
    assert len(res.papers) > 0
    first = res.papers[0]
    assert first.arxiv_id != ""
    assert first.title != ""
    assert len(first.authors) > 0

@pytest.mark.asyncio
async def test_clean_arxiv_id():
    assert arxiv_service.clean_arxiv_id("arXiv:2307.03172v3") == "2307.03172"
    assert arxiv_service.clean_arxiv_id("https://arxiv.org/abs/2401.15884") == "2401.15884"
