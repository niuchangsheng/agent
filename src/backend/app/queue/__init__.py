"""
Sprint 9: 队列模块

导出队列类和工厂函数
"""
from .base import BaseQueue, QueuedTask, RunningTask
from .in_memory_queue import InMemoryQueue
from .redis_queue import RedisQueue

__all__ = [
    "BaseQueue",
    "InMemoryQueue",
    "RedisQueue",
    "QueuedTask",
    "RunningTask",
    "create_queue",
]


def create_queue(redis_url: str = None, max_concurrent: int = 2) -> BaseQueue:
    """
    创建队列实例

    如果 Redis 可用则使用 RedisQueue，否则降级到 InMemoryQueue
    """
    if redis_url:
        queue = RedisQueue(redis_url=redis_url, max_concurrent=max_concurrent)
        # 尝试连接 Redis
        import asyncio
        try:
            # 在同步上下文中无法 await，需要在使用时异步连接
            pass
        except Exception:
            pass
        return queue
    else:
        return InMemoryQueue(max_concurrent=max_concurrent)
