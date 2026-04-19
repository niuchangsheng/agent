"""
SSE Broadcaster - Server-Sent Events 实时广播器

职责:
1. 管理客户端订阅连接
2. 向特定任务推送事件
3. 生成 SSE 格式流
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class SSEConnection:
    """单个 SSE 连接"""
    task_id: int
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_closed: bool = False

    async def put(self, event: dict):
        """添加事件到队列"""
        if not self.is_closed:
            await self.queue.put(event)

    async def get(self) -> dict:
        """获取下一个事件"""
        return await self.queue.get()

    def close(self):
        """关闭连接"""
        self.is_closed = True


class SSEBroadcaster:
    """SSE 事件广播器"""

    def __init__(self):
        self.connections: Dict[int, List[SSEConnection]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: int) -> SSEConnection:
        """订阅任务事件流"""
        connection = SSEConnection(task_id=task_id)

        async with self._lock:
            if task_id not in self.connections:
                self.connections[task_id] = []
            self.connections[task_id].append(connection)
            logger.info(f"SSE client subscribed to task {task_id}, total connections: {len(self.connections[task_id])}")

        return connection

    async def unsubscribe(self, connection: SSEConnection):
        """取消订阅"""
        async with self._lock:
            task_id = connection.task_id
            if task_id in self.connections:
                try:
                    self.connections[task_id].remove(connection)
                    connection.close()
                    logger.info(f"SSE client unsubscribed from task {task_id}")
                    if not self.connections[task_id]:
                        del self.connections[task_id]
                except ValueError:
                    pass  # 连接已不存在

    async def emit(self, task_id: int, event_type: str, data: dict):
        """向所有订阅该任务的连接推送事件"""
        async with self._lock:
            connections = self.connections.get(task_id, [])

        if not connections:
            logger.debug(f"No SSE connections for task {task_id}")
            return

        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        for conn in connections:
            try:
                await conn.put(event)
            except Exception as e:
                logger.warning(f"Failed to emit to connection: {e}")

        logger.debug(f"Emitting {event_type} to {len(connections)} connections for task {task_id}")

    async def emit_all(self, event_type: str, data: dict):
        """向所有连接推送事件"""
        async with self._lock:
            all_task_ids = list(self.connections.keys())

        for task_id in all_task_ids:
            await self.emit(task_id, event_type, data)

    def generate_stream(self, connection: SSEConnection) -> AsyncGenerator[str, None]:
        """生成 SSE 格式流"""
        async def stream_generator():
            try:
                # 发送初始连接事件
                yield f"event: connected\ndata: {{\"task_id\": {connection.task_id}}}\n\n"

                while not connection.is_closed:
                    try:
                        # 使用 timeout 避免无限等待
                        event = await asyncio.wait_for(connection.get(), timeout=30.0)
                        yield f"event: {event['type']}\ndata: {json.dumps(event['data'])}\n\n"
                    except asyncio.TimeoutError:
                        # 发送心跳保持连接
                        yield f"event: heartbeat\ndata: {{\"timestamp\": \"{datetime.now(timezone.utc).isoformat()}\"}}\n\n"
            except asyncio.CancelledError:
                logger.info(f"SSE stream cancelled for task {connection.task_id}")
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
            finally:
                connection.close()

        return stream_generator()

    async def get_status(self) -> dict:
        """获取广播器状态"""
        async with self._lock:
            return {
                "active_tasks": len(self.connections),
                "total_connections": sum(len(conns) for conns in self.connections.values()),
                "tasks": {
                    task_id: len(conns)
                    for task_id, conns in self.connections.items()
                }
            }


# 全局广播器实例
_global_broadcaster: Optional[SSEBroadcaster] = None


def init_sse_broadcaster() -> SSEBroadcaster:
    """初始化全局 SSE 广播器"""
    global _global_broadcaster
    _global_broadcaster = SSEBroadcaster()
    logger.info("SSE Broadcaster initialized")
    return _global_broadcaster


def get_sse_broadcaster() -> Optional[SSEBroadcaster]:
    """获取全局 SSE 广播器"""
    return _global_broadcaster