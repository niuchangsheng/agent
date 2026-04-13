"""
Sprint 9: Redis 队列测试套件
"""
import pytest
import asyncio
from datetime import datetime, timezone

from app.queue.base import QueuedTask, RunningTask
from app.queue.in_memory_queue import InMemoryQueue

# 尝试导入 Redis 队列
try:
    from app.queue.redis_queue import RedisQueue
    REDIS_AVAILABLE = True
except Exception:
    REDIS_AVAILABLE = False


@pytest.fixture
def memory_queue():
    """创建内存队列实例"""
    return InMemoryQueue(max_concurrent=2)


@pytest.fixture
async def redis_queue():
    """创建 Redis 队列实例（如果可用）"""
    if not REDIS_AVAILABLE:
        pytest.skip("Redis not available")

    queue = RedisQueue(redis_url="redis://localhost:6379", max_concurrent=2)
    connected = await queue.connect()
    if not connected:
        pytest.skip("Redis connection failed")

    # 清理测试数据
    await queue._redis.delete("seca:queue:pending")
    await queue._redis.delete("seca:queue:running")

    yield queue

    # 清理
    await queue.close()


@pytest.mark.asyncio
class TestInMemoryQueue:
    """内存队列测试套件"""

    async def test_enqueue_adds_to_queue(self, memory_queue):
        """Green 路径：入队添加任务"""
        position = await memory_queue.enqueue(1, 100, "Test objective")
        assert position == 1

        status = await memory_queue.get_status()
        assert len(status["queued"]) == 1
        assert status["queued"][0]["task_id"] == 1

    async def test_dequeue_removes_highest_priority(self, memory_queue):
        """Green 路径：出队取出最高优先级任务"""
        await memory_queue.enqueue(1, 100, "Low priority", priority=0)
        await memory_queue.enqueue(2, 100, "High priority", priority=5)
        await memory_queue.enqueue(3, 100, "Medium priority", priority=2)

        task = await memory_queue.dequeue()
        assert task.task_id == 2  # 最高优先级

        task = await memory_queue.dequeue()
        assert task.task_id == 3  # 中等优先级

        task = await memory_queue.dequeue()
        assert task.task_id == 1  # 低优先级

    async def test_dequeue_respects_concurrency_limit(self, memory_queue):
        """Red 路径：并发限制"""
        # 填满并发槽位
        await memory_queue.start_task(1, "worker-1")
        await memory_queue.start_task(2, "worker-2")

        await memory_queue.enqueue(3, 100, "Waiting task")

        # 不应取出任务（无可用槽位）
        task = await memory_queue.dequeue()
        assert task is None

    async def test_empty_queue_dequeue_returns_none(self, memory_queue):
        """Red 路径：空队列出队返回 None"""
        task = await memory_queue.dequeue()
        assert task is None

    async def test_same_priority_fifo_order(self, memory_queue):
        """Green 路径：相同优先级遵循 FIFO"""
        await memory_queue.enqueue(1, 100, "First task")
        await asyncio.sleep(0.01)
        await memory_queue.enqueue(2, 100, "Second task")

        task1 = await memory_queue.dequeue()
        task2 = await memory_queue.dequeue()

        assert task1.task_id == 1
        assert task2.task_id == 2

    async def test_start_task_marks_as_running(self, memory_queue):
        """Green 路径：启动任务标记为运行中"""
        await memory_queue.enqueue(1, 100, "Test task")
        await memory_queue.dequeue()

        result = await memory_queue.start_task(1, "worker-1")
        assert result is True

        status = await memory_queue.get_status()
        assert len(status["running"]) == 1
        assert status["running"][0]["task_id"] == 1

    async def test_start_task_already_running_returns_false(self, memory_queue):
        """Red 路径：任务已在运行"""
        await memory_queue.start_task(1, "worker-1")
        result = await memory_queue.start_task(1, "worker-2")
        assert result is False

    async def test_update_progress(self, memory_queue):
        """Green 路径：更新任务进度"""
        await memory_queue.start_task(1, "worker-1")

        result = await memory_queue.update_progress(1, 50, "Processing...")
        assert result is True

        status = await memory_queue.get_status()
        assert status["running"][0]["progress_percent"] == 50
        assert status["running"][0]["status_message"] == "Processing..."

    async def test_update_progress_task_not_running(self, memory_queue):
        """Red 路径：任务不在运行中"""
        result = await memory_queue.update_progress(1, 50, "Processing...")
        assert result is False

    async def test_complete_task(self, memory_queue):
        """Green 路径：完成任务"""
        await memory_queue.start_task(1, "worker-1")

        result = await memory_queue.complete_task(1)
        assert result is True

        status = await memory_queue.get_status()
        assert len(status["running"]) == 0

    async def test_complete_task_not_running(self, memory_queue):
        """Red 路径：任务不在运行中"""
        result = await memory_queue.complete_task(1)
        assert result is False

    async def test_cancel_task_from_queue(self, memory_queue):
        """Green 路径：取消队列中任务"""
        await memory_queue.enqueue(1, 100, "Test task")

        result = await memory_queue.cancel_task(1)
        assert result is True

        status = await memory_queue.get_status()
        assert len(status["queued"]) == 0

    async def test_cancel_task_from_running(self, memory_queue):
        """Green 路径：取消运行中任务"""
        await memory_queue.start_task(1, "worker-1")

        result = await memory_queue.cancel_task(1)
        assert result is True

        status = await memory_queue.get_status()
        assert len(status["running"]) == 0

    async def test_cancel_non_existent_task(self, memory_queue):
        """Red 路径：取消不存在任务"""
        result = await memory_queue.cancel_task(999)
        assert result is False

    async def test_requeue_on_crash(self, memory_queue):
        """Green 路径：Worker 崩溃后重新入队"""
        await memory_queue.start_task(1, "worker-1")

        result = await memory_queue.requeue_on_crash(1, 100, "Test task")
        assert result is True

        status = await memory_queue.get_status()
        assert len(status["queued"]) == 1
        assert len(status["running"]) == 0

    async def test_requeue_on_crash_task_not_running(self, memory_queue):
        """Red 路径：任务不在运行中"""
        result = await memory_queue.requeue_on_crash(1, 100, "Test task")
        assert result is False

    async def test_get_status(self, memory_queue):
        """Green 路径：获取队列状态"""
        await memory_queue.enqueue(1, 100, "Test task")
        await memory_queue.start_task(2, "worker-1")

        status = await memory_queue.get_status()

        assert status["max_concurrent"] == 2
        assert status["available_slots"] == 1
        assert len(status["queued"]) == 1
        assert len(status["running"]) == 1

    async def test_priority_order_with_mixed_priorities(self, memory_queue):
        """集成测试：混合优先级排序"""
        priorities = [0, 5, 2, 8, 1, 5]
        for i, p in enumerate(priorities):
            await memory_queue.enqueue(i + 1, 100, f"Task {i}", priority=p)
            await asyncio.sleep(0.001)  # 确保时间戳不同

        # 按优先级降序：8(3), 5(1), 5(5), 2(2), 1(4), 0(0)
        # 相同优先级按时间顺序
        task = await memory_queue.dequeue()
        assert task.task_id == 4  # 优先级 8

        task = await memory_queue.dequeue()
        assert task.task_id == 2  # 优先级 5，先入队

        task = await memory_queue.dequeue()
        assert task.task_id == 6  # 优先级 5，后入队


@pytest.mark.asyncio
class TestRedisQueue:
    """Redis 队列测试套件（如果 Redis 可用）"""

    @pytest.fixture(autouse=True)
    async def cleanup_redis(self, redis_queue):
        """每个测试前后清理 Redis 数据"""
        yield
        await redis_queue._redis.delete("seca:queue:pending")
        await redis_queue._redis.delete("seca:queue:running")

    async def test_redis_enqueue_adds_to_sorted_set(self, redis_queue):
        """Green 路径：入队添加到 Sorted Set"""
        position = await redis_queue.enqueue(1, 100, "Test objective")
        assert position == 1

        pending_count = await redis_queue._redis.zcard("seca:queue:pending")
        assert pending_count == 1

        task_data = await redis_queue._redis.hgetall("seca:queue:task:1")
        assert task_data["task_id"] == "1"
        assert task_data["project_id"] == "100"

    async def test_redis_dequeue_removes_highest_priority(self, redis_queue):
        """Green 路径：出队取出最高优先级"""
        await redis_queue.enqueue(1, 100, "Low priority", priority=0)
        await redis_queue.enqueue(2, 100, "High priority", priority=5)
        await redis_queue.enqueue(3, 100, "Medium priority", priority=2)

        task = await redis_queue.dequeue()
        assert task.task_id == 2

        task = await redis_queue.dequeue()
        assert task.task_id == 3

    async def test_redis_task_persistence(self, redis_queue):
        """集成测试：任务持久化"""
        await redis_queue.enqueue(1, 100, "Persistent task")

        # 模拟断开重连
        await redis_queue.close()
        await redis_queue.connect()

        # 任务仍应存在
        pending_count = await redis_queue._redis.zcard("seca:queue:pending")
        assert pending_count == 1

    async def test_redis_progress_update_persists(self, redis_queue):
        """Green 路径：进度更新持久化"""
        await redis_queue.start_task(1, "worker-1")

        result = await redis_queue.update_progress(1, 50, "Processing...")
        assert result is True

        # 验证持久化
        running_data_str = await redis_queue._redis.hget("seca:queue:running", "1")
        running_data = __import__("json").loads(running_data_str)
        assert running_data["progress_percent"] == "50"

    async def test_redis_queue_status(self, redis_queue):
        """Green 路径：队列状态查询"""
        await redis_queue.enqueue(1, 100, "Test task")
        await redis_queue.start_task(2, "worker-1")

        status = await redis_queue.get_status()

        assert len(status["queued"]) == 1
        assert len(status["running"]) == 1
        assert status["max_concurrent"] == 2

    async def test_redis_recovery_restores_running_tasks(self, redis_queue):
        """集成测试：崩溃恢复"""
        # 启动任务
        await redis_queue.start_task(1, "worker-1")
        await redis_queue.start_task(2, "worker-2")

        # 模拟崩溃恢复
        await redis_queue.recover_from_persistence()

        # 运行中任务应回到待处理队列
        status = await redis_queue.get_status()
        assert len(status["running"]) == 0
        assert len(status["queued"]) == 2

    async def test_redis_recovery_ignores_completed_tasks(self, redis_queue):
        """集成测试：已完成任务不恢复"""
        await redis_queue.start_task(1, "worker-1")
        await redis_queue.complete_task(1)

        # 恢复
        await redis_queue.recover_from_persistence()

        # 已完成任务不应出现
        status = await redis_queue.get_status()
        assert len(status["queued"]) == 0

    async def test_redis_cancel_task(self, redis_queue):
        """Green 路径：取消任务"""
        await redis_queue.enqueue(1, 100, "Test task")

        result = await redis_queue.cancel_task(1)
        assert result is True

        pending_count = await redis_queue._redis.zcard("seca:queue:pending")
        assert pending_count == 0

    async def test_redis_requeue_on_crash(self, redis_queue):
        """Green 路径：崩溃后重新入队"""
        await redis_queue.start_task(1, "worker-1")

        result = await redis_queue.requeue_on_crash(1, 100, "Test task")
        assert result is True

        status = await redis_queue.get_status()
        assert len(status["queued"]) == 1
        assert len(status["running"]) == 0
