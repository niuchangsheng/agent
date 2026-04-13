"""
Sprint 9: 队列抽象基类

定义队列接口规范，RedisQueue 和 InMemoryQueue 继承实现
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class QueuedTask:
    """队列中的任务"""
    task_id: int
    project_id: int
    raw_objective: str
    priority: int = 0
    queued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RunningTask:
    """运行中的任务"""
    task_id: int
    worker_id: str
    progress_percent: int = 0
    status_message: str = ""
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class BaseQueue(ABC):
    """队列抽象基类"""

    @abstractmethod
    async def enqueue(self, task_id: int, project_id: int, raw_objective: str, priority: int = 0) -> int:
        """添加任务到队列，返回队列位置"""
        pass

    @abstractmethod
    async def dequeue(self) -> Optional[QueuedTask]:
        """从队列取出一个任务（如果有可用槽位）"""
        pass

    @abstractmethod
    async def start_task(self, task_id: int, worker_id: str) -> bool:
        """标记任务为运行中"""
        pass

    @abstractmethod
    async def update_progress(self, task_id: int, progress_percent: int, status_message: str) -> bool:
        """更新任务进度"""
        pass

    @abstractmethod
    async def complete_task(self, task_id: int) -> bool:
        """标记任务为完成"""
        pass

    @abstractmethod
    async def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        pass

    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        pass

    @abstractmethod
    async def requeue_on_crash(self, task_id: int, project_id: int, raw_objective: str) -> bool:
        """Worker 崩溃后重新入队"""
        pass

    @abstractmethod
    async def recover_from_persistence(self) -> None:
        """从持久化存储恢复未完成任务"""
        pass
