import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_sse_endpoint_headers():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Simulate connecting to an active task's SSE channel
        response = await client.get("/api/v1/tasks/1/stream")
        assert response.status_code == 200
        # SSE 端点返回 text/event-stream
        assert "text/event-stream" in response.headers.get("content-type", "")

@pytest.mark.asyncio
async def test_sse_message_content():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # SSE 端点使用 event: xxx\ndata: xxx\n\n 格式
        async with client.stream("GET", "/api/v1/tasks/1/stream") as response:
            lines = []
            async for line in response.aiter_lines():
                if line:
                    lines.append(line)
                # Just read the first chunk to prevent hanging infinite stream for testing
                if len(lines) >= 3:
                    break

            # 新 SSE 格式：event: connected\ndata: {...}\n\n
            # 应该包含 event: 或 data: 行
            assert any("event:" in l or "data:" in l for l in lines)
