import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_sse_endpoint_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Simulate connecting to an active task's SSE channel
        response = await client.get("/api/v1/tasks/1/stream")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "text/event-stream; charset=utf-8"

@pytest.mark.asyncio
async def test_sse_message_content():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # We test that the generator yields standard SSE format (e.g. data: {"log": ...}\n\n)
        async with client.stream("GET", "/api/v1/tasks/1/stream") as response:
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(line)
                # Just read the first chunk to prevent hanging infinite stream for testing
                if len(lines) >= 1:
                    break
            
            assert any("data:" in l for l in lines)
