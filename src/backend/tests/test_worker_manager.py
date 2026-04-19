"""
测试 Worker Manager
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.worker.manager import WorkerManager
from app.queue import InMemoryQueue
from app.worker.sse_broadcaster import SSEBroadcaster


@pytest.mark.asyncio
async def test_worker_manager_creation():
    """测试 WorkerManager 创建"""
    queue = InMemoryQueue(max_concurrent=2)
    broadcaster = SSEBroadcaster()
    manager = WorkerManager(queue, max_concurrent=2, sse_broadcaster=broadcaster)

    assert manager.max_concurrent == 2
    assert manager.poll_interval == 1.0
    assert manager._running == False


@pytest.mark.asyncio
async def test_worker_manager_start_stop():
    """测试启动和停止"""
    queue = InMemoryQueue(max_concurrent=2)
    broadcaster = SSEBroadcaster()
    manager = WorkerManager(queue, max_concurrent=2, sse_broadcaster=broadcaster)

    await manager.start()
    status = await manager.get_status()
    assert status["running"] == True

    await manager.stop()
    status = await manager.get_status()
    assert status["running"] == False


@pytest.mark.asyncio
async def test_worker_manager_concurrent_limit():
    """测试并发限制"""
    queue = InMemoryQueue(max_concurrent=2)
    broadcaster = SSEBroadcaster()
    manager = WorkerManager(queue, max_concurrent=2, sse_broadcaster=broadcaster)

    # 入队 5 个任务
    for i in range(5):
        await queue.enqueue(i+1, 1, f"Task {i+1}")

    await manager.start()
    await asyncio.sleep(0.5)  # 等待轮询

    status = await manager.get_status()
    # 应该最多只有 2 个活跃 worker
    assert status["active_workers"] <= 2

    await manager.stop()


@pytest.mark.asyncio
async def test_worker_manager_generate_worker_id():
    """测试 Worker ID 生成"""
    queue = InMemoryQueue(max_concurrent=2)
    manager = WorkerManager(queue, max_concurrent=2)

    id1 = manager._generate_worker_id()
    id2 = manager._generate_worker_id()

    assert id1 != id2
    assert len(id1) == 8
    assert id1 in manager.worker_ids
    assert id2 in manager.worker_ids


@pytest.mark.asyncio
async def test_worker_manager_get_status():
    """测试状态获取"""
    queue = InMemoryQueue(max_concurrent=2)
    broadcaster = SSEBroadcaster()
    manager = WorkerManager(queue, max_concurrent=2, sse_broadcaster=broadcaster)

    await manager.start()
    status = await manager.get_status()

    assert "running" in status
    assert "max_concurrent" in status
    assert "active_workers" in status
    assert status["max_concurrent"] == 2

    await manager.stop()


@pytest.mark.asyncio
async def test_worker_manager_poll_loop():
    """测试轮询循环"""
    queue = InMemoryQueue(max_concurrent=2)
    broadcaster = SSEBroadcaster()
    manager = WorkerManager(queue, max_concurrent=2, poll_interval=0.1, sse_broadcaster=broadcaster)

    # Mock AgentEngine 来避免真实执行
    with patch('app.worker.manager.AgentEngine') as mock_engine_class:
        mock_engine = MagicMock()
        mock_engine.run = AsyncMock(return_value={"success": True, "message": "Test complete"})
        mock_engine_class.return_value = mock_engine

        await manager.start()

        # 入队任务
        await queue.enqueue(1, 1, "Test task")

        await asyncio.sleep(0.5)  # 等待轮询

        # 验证任务被取出
        status = await manager.get_status()
        # 可能有任务正在处理
        assert status["running"] == True

        await manager.stop()