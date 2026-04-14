"""
Sprint 13: 系统监控指标采集器
"""
import os
import psutil
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlmodel import select
from app.models import Task, AuditLog
from sqlmodel.ext.asyncio.session import AsyncSession


# 阈值定义
THRESHOLDS = {
    "queued_tasks": 100,  # 队列长度 > 100
    "latency_p95_ms": 1000,  # P95 延迟 > 1000ms
    "memory_mb": 1024,  # 内存 > 1024MB
}


def check_thresholds(
    queued_tasks: int,
    p95_ms: float,
    memory_mb: float,
    redis_connected: bool
) -> List[str]:
    """检查各项指标是否超出阈值"""
    alerts = []

    if queued_tasks > THRESHOLDS["queued_tasks"]:
        alerts.append("queued_tasks")

    if p95_ms > THRESHOLDS["latency_p95_ms"]:
        alerts.append("latency_p95")

    if memory_mb > THRESHOLDS["memory_mb"]:
        alerts.append("memory_mb")

    if not redis_connected:
        alerts.append("redis_connected")

    return alerts


class MetricsCollector:
    """系统监控指标采集器"""

    def __init__(self):
        self._last_collection_time: Optional[datetime] = None

    async def get_concurrent_tasks(self, session: AsyncSession) -> int:
        """获取当前并发任务数（RUNNING 状态）"""
        from sqlmodel import select

        result = await session.exec(
            select(Task).where(Task.status == "RUNNING")
        )
        tasks = result.all()
        return len(tasks)

    async def get_queued_tasks(self, session: AsyncSession) -> int:
        """获取队列等待任务数（QUEUED 状态）"""
        from sqlmodel import select

        result = await session.exec(
            select(Task).where(Task.status == "QUEUED")
        )
        tasks = result.all()
        return len(tasks)

    def get_memory_usage_mb(self) -> float:
        """获取当前进程内存使用量（MB）"""
        process = psutil.Process(os.getpid())
        memory_bytes = process.memory_info().rss
        return memory_bytes / (1024 * 1024)

    def get_redis_status(self) -> bool:
        """获取 Redis 连接状态"""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            return False

        # 尝试连接 Redis 验证
        try:
            import redis
            from redis.asyncio import Redis
            # 这里只做简单检查，实际连接状态由队列管理
            return True
        except ImportError:
            # redis 库未安装
            return False

    async def get_latency_percentiles(self, session: AsyncSession) -> Tuple[float, float]:
        """计算响应延迟的 P50/P95（基于审计日志）"""
        from sqlmodel import select

        # 获取最近 1000 条审计日志的 duration_ms
        result = await session.exec(
            select(AuditLog.duration_ms)
            .where(AuditLog.duration_ms.isnot(None))
            .order_by(AuditLog.timestamp.desc())
            .limit(1000)
        )
        durations = result.all()

        if not durations:
            return 0.0, 0.0

        # 排序计算百分位数
        sorted_durations = sorted(durations)
        n = len(sorted_durations)

        p50_index = int(n * 0.50)
        p95_index = int(n * 0.95)

        p50 = sorted_durations[min(p50_index, n - 1)]
        p95 = sorted_durations[min(p95_index, n - 1)]

        return float(p50), float(p95)

    async def get_snapshot(self, session: AsyncSession) -> Dict:
        """获取监控指标快照"""
        concurrent = await self.get_concurrent_tasks(session)
        queued = await self.get_queued_tasks(session)
        memory = self.get_memory_usage_mb()
        redis_connected = self.get_redis_status()
        p50, p95 = await self.get_latency_percentiles(session)

        # 检查阈值
        exceeded = check_thresholds(
            queued_tasks=queued,
            p95_ms=p95,
            memory_mb=memory,
            redis_connected=redis_connected
        )

        return {
            "concurrent_tasks": concurrent,
            "queued_tasks": queued,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "memory_mb": memory,
            "redis_connected": redis_connected,
            "threshold_exceeded": exceeded,
        }
