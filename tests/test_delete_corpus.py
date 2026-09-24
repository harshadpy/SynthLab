import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app

@pytest.mark.asyncio
async def test_delete_corpus_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a corpus
        res = await client.post("/api/corpora", json={
            "name": "Temporary Test Corpus",
            "query": "test query",
            "paper_ids": ["2307.03172"]
        })
        assert res.status_code == 200
        corpus_id = res.json()["id"]

        # Delete the corpus
        del_res = await client.delete(f"/api/corpora/{corpus_id}")
        assert del_res.status_code == 200
        assert del_res.json()["deleted"] is True

        # Verify it no longer exists
        get_res = await client.get(f"/api/corpora/{corpus_id}")
        assert get_res.status_code == 404
