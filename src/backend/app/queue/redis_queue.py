"""
Sprint 9: Redis 队列实现

基于 Redis 的持久化任务队列
"""
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from .base import BaseQueue, QueuedTask, RunningTask

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False


class RedisQueue(BaseQueue):
    """Redis 队列实现 - 持久化模式"""

    # Redis Key 前缀
    KEY_PREFIX = "seca:queue"
    PENDING_KEY = f"{KEY_PREFIX}:pending"  # Sorted Set
    RUNNING_KEY = f"{KEY_PREFIX}:running"  # Hash
    TASK_PREFIX = f"{KEY_PREFIX}:task"  # Hash: task:{id}

    def __init__(self, redis_url: str = "redis://localhost:6379", max_concurrent: int = 2):
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis-py not installed")

        self.redis_url = redis_url
        self.max_concurrent = max_concurrent
        self._redis: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        self._connected = False

    async def connect(self) -> bool:
        """连接 Redis，失败返回 False"""
        try:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5.0
            )
            await self._redis.ping()
            self._connected = True
            logger.info(f"Connected to Redis: {self.redis_url}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Falling back to memory queue.")
            self._connected = False
            return False

    async def close(self):
        """关闭 Redis 连接"""
        if self._redis:
            await self._redis.close()
            self._connected = False

    def _task_score(self, priority: int, queued_at: datetime) -> float:
        """计算任务在 Sorted Set 中的分数（优先级高的在前）"""
        # 使用负优先级 + 时间戳，确保优先级高的在前，同优先级则先到先出
        return -priority * 1e10 + queued_at.timestamp()

    async def enqueue(self, task_id: int, project_id: int, raw_objective: str, priority: int = 0) -> int:
        """添加任务到队列，返回队列位置"""
        async with self._lock:
            if not self._connected:
                logger.warning("Redis not connected, enqueue ignored")
                return -1

            queued_at = datetime.now(timezone.utc)
            task_data = {
                "task_id": str(task_id),
                "project_id": str(project_id),
                "raw_objective": raw_objective,
                "priority": str(priority),
                "queued_at": queued_at.isoformat()
            }

            # 添加到任务详情 Hash
            await self._redis.hset(f"{self.TASK_PREFIX}:{task_id}", mapping=task_data)

            # 添加到待处理 Sorted Set
            score = self._task_score(priority, queued_at)
            await self._redis.zadd(self.PENDING_KEY, {str(task_id): score})

            # 获取队列位置
            position = await self._redis.zrank(self.PENDING_KEY, str(task_id))
            return (position or 0) + 1

    async def dequeue(self) -> Optional[QueuedTask]:
        """从队列取出一个任务（如果有可用槽位）"""
        async with self._lock:
            if not self._connected:
                return None

            # 检查运行中任务数
            running_count = await self._redis.hlen(self.RUNNING_KEY)
            if running_count >= self.max_concurrent:
                return None

            # 获取优先级最高的任务
            task_ids = await self._redis.zpopmin(self.PENDING_KEY, count=1)
            if not task_ids:
                return None

            task_id = int(task_ids[0][0])

            # 获取任务详情
            task_data = await self._redis.hgetall(f"{self.TASK_PREFIX}:{task_id}")
            if not task_data:
                return None

            return QueuedTask(
                task_id=task_id,
                project_id=int(task_data["project_id"]),
                raw_objective=task_data["raw_objective"],
                priority=int(task_data.get("priority", 0)),
                queued_at=datetime.fromisoformat(task_data["queued_at"])
            )

    async def start_task(self, task_id: int, worker_id: str) -> bool:
        """标记任务为运行中"""
        async with self._lock:
            if not self._connected:
                return False

            # 检查是否已在运行
            exists = await self._redis.hexists(self.RUNNING_KEY, str(task_id))
            if exists:
                return False

            task_data = await self._redis.hgetall(f"{self.TASK_PREFIX}:{task_id}")
            if not task_data:
                return False

            running_data = {
                "task_id": str(task_id),
                "worker_id": worker_id,
                "progress_percent": "0",
                "status_message": "",
                "started_at": datetime.now(timezone.utc).isoformat(),
                **task_data
            }
            await self._redis.hset(self.RUNNING_KEY, str(task_id), json.dumps(running_data))
            return True

    async def update_progress(self, task_id: int, progress_percent: int, status_message: str) -> bool:
        """更新任务进度"""
        async with self._lock:
            if not self._connected:
                return False

            running_data_str = await self._redis.hget(self.RUNNING_KEY, str(task_id))
            if not running_data_str:
                return False

            running_data = json.loads(running_data_str)
            running_data["progress_percent"] = str(progress_percent)
            running_data["status_message"] = status_message

            await self._redis.hset(self.RUNNING_KEY, str(task_id), json.dumps(running_data))

            # 同时更新任务详情
            await self._redis.hset(
                f"{self.TASK_PREFIX}:{task_id}",
                mapping={"progress_percent": str(progress_percent), "status_message": status_message}
            )
            return True

    async def complete_task(self, task_id: int) -> bool:
        """标记任务为完成"""
        async with self._lock:
            if not self._connected:
                return False

            # 从运行中移除
            result = await self._redis.hdel(self.RUNNING_KEY, str(task_id))
            if result == 0:
                return False

            # 清理任务详情（可选：保留一段时间用于审计）
            await self._redis.delete(f"{self.TASK_PREFIX}:{task_id}")
            return True

    async def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        async with self._lock:
            if not self._connected:
                return False

            # 从待处理中移除
            await self._redis.zrem(self.PENDING_KEY, str(task_id))

            # 从运行中移除
            result = await self._redis.hdel(self.RUNNING_KEY, str(task_id))

            # 清理任务详情
            await self._redis.delete(f"{self.TASK_PREFIX}:{task_id}")

            return result > 0

    async def get_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        async with self._lock:
            if not self._connected:
                return {
                    "queued": [],
                    "running": [],
                    "max_concurrent": self.max_concurrent,
                    "available_slots": self.max_concurrent,
                    "error": "Redis not connected"
                }

            # 获取待处理任务
            pending_ids = await self._redis.zrange(self.PENDING_KEY, 0, -1, withscores=True)
            queued = []
            for i, (task_id, score) in enumerate(pending_ids):
                task_data = await self._redis.hgetall(f"{self.TASK_PREFIX}:{task_id}")
                if task_data:
                    queued.append({
                        "task_id": int(task_data["task_id"]),
                        "project_id": int(task_data["project_id"]),
                        "raw_objective": task_data["raw_objective"],
                        "priority": int(task_data.get("priority", 0)),
                        "queued_at": task_data.get("queued_at", ""),
                        "position": i + 1
                    })

            # 获取运行中任务
            running_items = await self._redis.hgetall(self.RUNNING_KEY)
            running = []
            for task_id, running_data_str in running_items.items():
                running_data = json.loads(running_data_str)
                running.append({
                    "task_id": int(running_data["task_id"]),
                    "worker_id": running_data["worker_id"],
                    "progress_percent": int(running_data.get("progress_percent", 0)),
                    "status_message": running_data.get("status_message", ""),
                    "started_at": running_data.get("started_at", "")
                })

            return {
                "queued": queued,
                "running": running,
                "max_concurrent": self.max_concurrent,
                "available_slots": self.max_concurrent - len(running)
            }

    async def requeue_on_crash(self, task_id: int, project_id: int, raw_objective: str) -> bool:
        """Worker 崩溃后重新入队"""
        async with self._lock:
            if not self._connected:
                return False

            # 从运行中移除
            result = await self._redis.hdel(self.RUNNING_KEY, str(task_id))
            if result == 0:
                return False

            # 重新加入待处理队列
            queued_at = datetime.now(timezone.utc)
            await self._redis.zadd(self.PENDING_KEY, {str(task_id): self._task_score(0, queued_at)})

            # 更新任务详情
            await self._redis.hset(
                f"{self.TASK_PREFIX}:{task_id}",
                mapping={
                    "task_id": str(task_id),
                    "project_id": str(project_id),
                    "raw_objective": raw_objective,
                    "priority": "0",
                    "queued_at": queued_at.isoformat()
                }
            )
            return True

    async def update_priority(self, task_id: int, new_priority: int) -> bool:
        """更新任务优先级"""
        async with self._lock:
            if not self._connected:
                return False

            # 检查是否在待处理队列中
            score = await self._redis.zscore(self.PENDING_KEY, str(task_id))
            if score is not None:
                # 在待处理队列中，更新分数
                # 获取原有 queued_at
                task_data = await self._redis.hgetall(f"{self.TASK_PREFIX}:{task_id}")
                if task_data:
                    queued_at = datetime.fromisoformat(task_data["queued_at"])
                    new_score = self._task_score(new_priority, queued_at)
                    await self._redis.zadd(self.PENDING_KEY, {str(task_id): new_score})
                    await self._redis.hset(f"{self.TASK_PREFIX}:{task_id}", "priority", str(new_priority))
                    return True
                return False

            # 检查是否在运行中（运行中任务也可以更新优先级记录）
            running = await self._redis.hexists(self.RUNNING_KEY, str(task_id))
            if running:
                running_data_str = await self._redis.hget(self.RUNNING_KEY, str(task_id))
                if running_data_str:
                    running_data = json.loads(running_data_str)
                    running_data["priority"] = str(new_priority)
                    await self._redis.hset(self.RUNNING_KEY, str(task_id), json.dumps(running_data))
                    await self._redis.hset(f"{self.TASK_PREFIX}:{task_id}", "priority", str(new_priority))
                    return True

            return False

    async def recover_from_persistence(self) -> None:
        """从持久化存储恢复未完成任务"""
        async with self._lock:
            if not self._connected:
                logger.warning("Cannot recover: Redis not connected")
                return

            # 恢复运行中任务到待处理队列（模拟崩溃恢复）
            running_items = await self._redis.hgetall(self.RUNNING_KEY)
            for task_id, running_data_str in running_items.items():
                running_data = json.loads(running_data_str)
                task_id_int = int(task_id)

                # 重新加入待处理队列
                queued_at = datetime.now(timezone.utc)
                await self._redis.zadd(
                    self.PENDING_KEY,
                    {str(task_id_int): self._task_score(0, queued_at)}
                )

                # 更新任务详情
                await self._redis.hset(
                    f"{self.TASK_PREFIX}:{task_id_int}",
                    mapping={
                        "task_id": str(task_id_int),
                        "project_id": running_data.get("project_id", "0"),
                        "raw_objective": running_data.get("raw_objective", ""),
                        "priority": "0",
                        "queued_at": queued_at.isoformat()
                    }
                )
                logger.info(f"Recovered running task {task_id_int} to pending queue")

            # 清理待处理任务的过期数据
            logger.info(f"Recovery complete. Pending: {await self._redis.zcard(self.PENDING_KEY)}")
