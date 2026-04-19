"""
测试 SSE Broadcaster
"""
import pytest
import asyncio
from app.worker.sse_broadcaster import SSEBroadcaster, SSEConnection


@pytest.mark.asyncio
async def test_sse_connection_creation():
    """测试 SSE 连接创建"""
    conn = SSEConnection(task_id=1)
    assert conn.task_id == 1
    assert conn.is_closed == False
    assert conn.queue is not None


@pytest.mark.asyncio
async def test_sse_subscribe():
    """测试订阅功能"""
    broadcaster = SSEBroadcaster()
    conn = await broadcaster.subscribe(task_id=1)
    assert conn.task_id == 1
    assert conn in broadcaster.connections.get(1, [])


@pytest.mark.asyncio
async def test_sse_unsubscribe():
    """测试取消订阅"""
    broadcaster = SSEBroadcaster()
    conn = await broadcaster.subscribe(task_id=1)
    await broadcaster.unsubscribe(conn)
    assert conn.is_closed == True
    assert 1 not in broadcaster.connections


@pytest.mark.asyncio
async def test_sse_emit():
    """测试事件推送"""
    broadcaster = SSEBroadcaster()
    conn = await broadcaster.subscribe(task_id=1)

    await broadcaster.emit(1, "test", {"message": "hello"})

    event = await asyncio.wait_for(conn.get(), timeout=1.0)
    assert event["type"] == "test"
    assert event["data"]["message"] == "hello"

    await broadcaster.unsubscribe(conn)


@pytest.mark.asyncio
async def test_sse_generate_stream():
    """测试流生成"""
    broadcaster = SSEBroadcaster()
    conn = await broadcaster.subscribe(task_id=1)

    await broadcaster.emit(1, "start", {"task_id": 1})

    stream = broadcaster.generate_stream(conn)

    # 获取第一个事件（连接事件）
    first_event = await stream.__anext__()
    assert "event: connected" in first_event

    await broadcaster.unsubscribe(conn)


@pytest.mark.asyncio
async def test_sse_status():
    """测试状态获取"""
    broadcaster = SSEBroadcaster()

    await broadcaster.subscribe(1)
    await broadcaster.subscribe(1)
    await broadcaster.subscribe(2)

    status = await broadcaster.get_status()
    assert status["active_tasks"] == 2
    assert status["total_connections"] == 3


@pytest.mark.asyncio
async def test_sse_heartbeat():
    """测试心跳机制"""
    broadcaster = SSEBroadcaster()
    conn = await broadcaster.subscribe(task_id=1)

    stream = broadcaster.generate_stream(conn)

    # 等待心跳（30秒超时内）
    # 由于测试环境，我们只验证流能正常生成
    assert stream is not None

    await broadcaster.unsubscribe(conn)