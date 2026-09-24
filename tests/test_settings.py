import pytest
from httpx import AsyncClient, ASGITransport
from apps.api.main import app

@pytest.mark.asyncio
async def test_settings_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get settings
        get_res = await client.get("/api/settings")
        assert get_res.status_code == 200
        data = get_res.json()
        assert "default_chat_model" in data
        assert "default_embedding_model" in data
        assert "langchain_project" in data

        # Update settings
        update_res = await client.post("/api/settings", json={
            "default_chat_model": "gpt-4o",
            "default_embedding_model": "text-embedding-3-large",
            "langchain_tracing_v2": True
        })
        assert update_res.status_code == 200
        assert update_res.json()["status"] == "success"
