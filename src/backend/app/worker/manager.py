"""
WorkerManager - 后台任务执行调度器

职责:
1. 从队列 dequeue 任务
2. 分配给 AgentEngine 执行
3. 管理并发控制 (max_concurrent)
4. 处理任务完成/失败/崩溃
"""
import asyncio
import logging
import uuid
import os
from typing import Optional, Dict, Set
from datetime import datetime, timezone

from app.queue import BaseQueue, QueuedTask
from app.worker.sse_broadcaster import SSEBroadcaster, get_sse_broadcaster
from app.worker.agent_engine import AgentEngine
from app.database import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models import Task, Project

logger = logging.getLogger(__name__)


class WorkerManager:
    """Worker 进程管理器"""

    def __init__(
        self,
        queue: BaseQueue,
        max_concurrent: int = 2,
        poll_interval: float = 1.0,
        sse_broadcaster: Optional[SSEBroadcaster] = None
    ):
        self.queue = queue
        self.max_concurrent = max_concurrent
        self.poll_interval = poll_interval
        self.sse_broadcaster = sse_broadcaster or get_sse_broadcaster()

        self.active_workers: Dict[int, asyncio.Task] = {}  # task_id -> asyncio.Task
        self.worker_ids: Set[str] = set()  # 活跃 worker_id 集合
        self._running = False
        self._poll_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动 Worker Manager"""
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"Worker Manager started with max_concurrent={self.max_concurrent}")

    async def stop(self):
        """停止 Worker Manager"""
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        # 等待所有活跃 Worker 完成
        for task_id, worker_task in list(self.active_workers.items()):
            logger.info(f"Waiting for task {task_id} to complete...")
            try:
                await asyncio.wait_for(worker_task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning(f"Task {task_id} did not complete in time, cancelling")
                worker_task.cancel()
            except asyncio.CancelledError:
                pass

        logger.info("Worker Manager stopped")

    def _generate_worker_id(self) -> str:
        """生成唯一 Worker ID"""
        worker_id = str(uuid.uuid4())[:8]
        while worker_id in self.worker_ids:
            worker_id = str(uuid.uuid4())[:8]
        self.worker_ids.add(worker_id)
        return worker_id

    async def _poll_loop(self):
        """轮询队列的主循环"""
        logger.info("Worker poll loop started")

        while self._running:
            try:
                # 检查是否有可用槽位
                if len(self.active_workers) >= self.max_concurrent:
                    await asyncio.sleep(self.poll_interval)
                    continue

                # 尝试 dequeue 任务
                queued_task = await self.queue.dequeue()
                if not queued_task:
                    await asyncio.sleep(self.poll_interval)
                    continue

                logger.info(f"Dequeued task {queued_task.task_id}: {queued_task.raw_objective}")

                # 启动任务执行
                worker_id = self._generate_worker_id()
                await self.queue.start_task(queued_task.task_id, worker_id)

                # 更新数据库状态
                async with AsyncSession(engine) as session:
                    task = await session.get(Task, queued_task.task_id)
                    if task:
                        task.status = "RUNNING"
                        task.worker_id = worker_id
                        task.started_at = datetime.now(timezone.utc)
                        task.queue_position = None
                        session.add(task)
                        await session.commit()

                # 推送 SSE 事件
                if self.sse_broadcaster:
                    await self.sse_broadcaster.emit(
                        queued_task.task_id,
                        "start",
                        {
                            "worker_id": worker_id,
                            "objective": queued_task.raw_objective,
                            "started_at": datetime.now(timezone.utc).isoformat()
                        }
                    )

                # 获取项目路径
                async with AsyncSession(engine) as session:
                    project = await session.get(Project, queued_task.project_id)
                    project_path = project.target_repo_path if project else os.getcwd()

                # 创建 AgentEngine 并执行
                engine_instance = AgentEngine(
                    task_id=queued_task.task_id,
                    project_id=queued_task.project_id,
                    project_path=project_path,
                    raw_objective=queued_task.raw_objective,
                    worker_id=worker_id,
                    sse_broadcaster=self.sse_broadcaster
                )

                worker_task = asyncio.create_task(
                    self._run_engine(queued_task.task_id, engine_instance, worker_id)
                )
                self.active_workers[queued_task.task_id] = worker_task

            except Exception as e:
                logger.error(f"Poll loop error: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)

    async def _run_engine(
        self,
        task_id: int,
        agent_engine: AgentEngine,
        worker_id: str
    ):
        """运行 AgentEngine 并处理结果"""
        try:
            result = await agent_engine.run()

            # 标记完成
            await self.queue.complete_task(task_id)

            # 更新数据库
            async with AsyncSession(engine) as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = "COMPLETED"
                    task.completed_at = datetime.now(timezone.utc)
                    task.progress_percent = 100
                    task.status_message = result.get("message", "Task completed")
                    session.add(task)
                    await session.commit()

            # 推送 SSE 完成事件
            if self.sse_broadcaster:
                await self.sse_broadcaster.emit(
                    task_id,
                    "complete",
                    {
                        "result": result,
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }
                )

            logger.info(f"Task {task_id} completed successfully")

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)

            # 重新入队或标记失败
            async with AsyncSession(engine) as session:
                task = await session.get(Task, task_id)
                if task:
                    task.status = "FAILED"
                    task.status_message = str(e)
                    session.add(task)
                    await session.commit()

            # 推送 SSE 错误事件
            if self.sse_broadcaster:
                await self.sse_broadcaster.emit(
                    task_id,
                    "error",
                    {
                        "error": str(e),
                        "worker_id": worker_id
                    }
                )

        finally:
            # 清理
            if task_id in self.active_workers:
                del self.active_workers[task_id]
            if worker_id in self.worker_ids:
                self.worker_ids.remove(worker_id)

    async def get_status(self) -> dict:
        """获取 Worker Manager 状态"""
        return {
            "running": self._running,
            "max_concurrent": self.max_concurrent,
            "active_workers": len(self.active_workers),
            "active_task_ids": list(self.active_workers.keys()),
            "worker_ids": list(self.worker_ids),
            "poll_interval": self.poll_interval
        }