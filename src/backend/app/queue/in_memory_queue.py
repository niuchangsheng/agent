"""
Sprint 9: 内存队列实现（降级模式）

当 Redis 不可用时使用的降级队列
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .base import BaseQueue, QueuedTask, RunningTask


class InMemoryQueue(BaseQueue):
    """内存队列实现 - 降级模式"""

    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.queued: List[QueuedTask] = []  # 等待队列
        self.running: Dict[int, RunningTask] = {}  # 运行中任务 {task_id: RunningTask}
        self._lock = asyncio.Lock()

    async def enqueue(self, task_id: int, project_id: int, raw_objective: str, priority: int = 0) -> int:
        """添加任务到队列，返回队列位置"""
        async with self._lock:
            # 按优先级和时间排序，优先级高的在前
            position = len(self.queued) + 1
            self.queued.append(QueuedTask(
                task_id=task_id,
                project_id=project_id,
                raw_objective=raw_objective,
                priority=priority
            ))
            return position

    async def dequeue(self) -> Optional[QueuedTask]:
        """从队列取出一个任务（如果有可用槽位）"""
        async with self._lock:
            if len(self.running) >= self.max_concurrent:
                return None  # 无可用槽位
            if not self.queued:
                return None  # 队列为空
            # 取出优先级最高的任务（优先级相同则 FIFO）
            self.queued.sort(key=lambda x: (-x.priority, x.queued_at))
            return self.queued.pop(0)

    async def start_task(self, task_id: int, worker_id: str) -> bool:
        """标记任务为运行中"""
        async with self._lock:
            if task_id in self.running:
                return False  # 任务已在运行
            self.running[task_id] = RunningTask(
                task_id=task_id,
                worker_id=worker_id
            )
            return True

    async def update_progress(self, task_id: int, progress_percent: int, status_message: str) -> bool:
        """更新任务进度"""
        async with self._lock:
            if task_id not in self.running:
                return False  # 任务不在运行中
            self.running[task_id].progress_percent = progress_percent
            self.running[task_id].status_message = status_message
            return True

    async def complete_task(self, task_id: int) -> bool:
        """标记任务为完成"""
        async with self._lock:
            if task_id not in self.running:
                return False
            del self.running[task_id]
            return True

    async def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        async with self._lock:
            # 从等待队列移除
            for i, qt in enumerate(self.queued):
                if qt.task_id == task_id:
                    self.queued.pop(i)
                    return True
            # 从运行中取消
            if task_id in self.running:
                del self.running[task_id]
                return True
            return False

    async def get_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        async with self._lock:
            return {
                "queued": [
                    {
                        "task_id": qt.task_id,
                        "project_id": qt.project_id,
                        "raw_objective": qt.raw_objective,
                        "priority": qt.priority,
                        "queued_at": qt.queued_at.isoformat(),
                        "position": i + 1
                    }
                    for i, qt in enumerate(self.queued)
                ],
                "running": [
                    {
                        "task_id": rt.task_id,
                        "worker_id": rt.worker_id,
                        "progress_percent": rt.progress_percent,
                        "status_message": rt.status_message,
                        "started_at": rt.started_at.isoformat()
                    }
                    for rt in self.running.values()
                ],
                "max_concurrent": self.max_concurrent,
                "available_slots": self.max_concurrent - len(self.running)
            }

    async def requeue_on_crash(self, task_id: int, project_id: int, raw_objective: str) -> bool:
        """Worker 崩溃后重新入队"""
        async with self._lock:
            if task_id not in self.running:
                return False
            # 从运行中移除，重新加入队列末尾
            self.running.pop(task_id)
            self.queued.append(QueuedTask(
                task_id=task_id,
                project_id=project_id,
                raw_objective=raw_objective
            ))
            return True

    async def recover_from_persistence(self) -> None:
        """从持久化存储恢复未完成任务"""
        # 内存队列无持久化，此方法为空操作
        pass
