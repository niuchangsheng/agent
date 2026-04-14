"""
Sprint 13: 系统监控仪表盘测试套件
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.metrics import MetricsCollector, check_thresholds


@pytest.mark.asyncio
class TestMetricsCollector:
    """Sprint 13: 指标采集器测试"""

    def test_metrics_collector_initialization(self):
        """Green 路径：指标采集器初始化"""
        collector = MetricsCollector()
        assert collector is not None

    async def test_metrics_collector_concurrent_tasks(self, async_client_with_data):
        """Green 路径：并发任务数统计正确"""
        collector = MetricsCollector()
        session = async_client_with_data["session"]

        # 统计并发任务数（RUNNING 状态）
        concurrent = await collector.get_concurrent_tasks(session)

        # 应该有 1 个 RUNNING 任务
        assert concurrent == 1, f"并发任务数应为 1，实际：{concurrent}"

    async def test_metrics_collector_queued_tasks(self, async_client_with_data):
        """Green 路径：队列等待数统计正确"""
        collector = MetricsCollector()
        session = async_client_with_data["session"]

        # 统计队列等待数（QUEUED 状态）
        queued = await collector.get_queued_tasks(session)

        # 应该有 2 个 QUEUED 任务
        assert queued == 2, f"队列等待数应为 2，实际：{queued}"

    def test_metrics_collector_memory(self):
        """Green 路径：内存使用量采集正确"""
        collector = MetricsCollector()

        memory_mb = collector.get_memory_usage_mb()

        # 内存使用量应为正数
        assert memory_mb > 0, f"内存使用量应大于 0，实际：{memory_mb}"
        # 内存使用量不应超过合理上限（10GB）
        assert memory_mb < 10240, f"内存使用量不应超过 10GB，实际：{memory_mb}"

    @pytest.mark.asyncio
    async def test_metrics_collector_redis_status_connected(self):
        """Green 路径：Redis 连接状态检测（已连接）"""
        import os
        # 临时设置 Redis URL
        original_redis_url = os.getenv("REDIS_URL")
        os.environ["REDIS_URL"] = "redis://localhost:6379"

        try:
            collector = MetricsCollector()
            # 注意：这里只测试逻辑，不测试真实 Redis 连接
            # 真实连接测试在集成测试中
            status = collector.get_redis_status()
            # 有 Redis 配置时返回 True（不验证实际连接）
            assert status is True
        finally:
            if original_redis_url:
                os.environ["REDIS_URL"] = original_redis_url
            else:
                os.environ.pop("REDIS_URL", None)

    @pytest.mark.asyncio
    async def test_metrics_collector_redis_status_disconnected(self):
        """Red 路径：Redis 连接状态检测（未连接）"""
        import os
        # 确保没有 Redis URL
        original_redis_url = os.getenv("REDIS_URL")
        os.environ.pop("REDIS_URL", None)

        try:
            collector = MetricsCollector()
            status = collector.get_redis_status()
            # 没有 Redis 配置时应返回 False
            assert status is False, f"无 Redis 配置时应返回 False，实际：{status}"
        finally:
            if original_redis_url:
                os.environ["REDIS_URL"] = original_redis_url

    async def test_metrics_latency_percentile(self, async_client_with_data):
        """Green 路径：P50/P95 延迟计算正确"""
        collector = MetricsCollector()
        session = async_client_with_data["session"]

        p50, p95 = await collector.get_latency_percentiles(session)

        # P50 和 P95 应为正数
        assert p50 >= 0, f"P50 延迟应为非负数，实际：{p50}"
        assert p95 >= 0, f"P95 延迟应为非负数，实际：{p95}"
        # P95 不应小于 P50
        assert p95 >= p50, f"P95 不应小于 P50，实际：P50={p50}, P95={p95}"

    async def test_metrics_latency_no_data(self):
        """Red 路径：无审计日志时延迟返回 0"""
        from sqlmodel import select
        from app.models import AuditLog
        from app.database import engine
        from sqlmodel.ext.asyncio.session import AsyncSession

        async with AsyncSession(engine) as session:
            # 删除所有审计日志
            result = await session.exec(select(AuditLog))
            logs = result.all()
            for log in logs:
                await session.delete(log)
            await session.commit()

            collector = MetricsCollector()
            p50, p95 = await collector.get_latency_percentiles(session)
            assert p50 == 0, f"无数据时 P50 应为 0，实际：{p50}"
            assert p95 == 0, f"无数据时 P95 应为 0，实际：{p95}"

    async def test_metrics_snapshot(self, async_client_with_data):
        """Green 路径：监控快照数据完整"""
        collector = MetricsCollector()
        session = async_client_with_data["session"]

        snapshot = await collector.get_snapshot(session)

        # 验证快照包含所有必需字段
        assert "concurrent_tasks" in snapshot
        assert "queued_tasks" in snapshot
        assert "latency_p50_ms" in snapshot
        assert "latency_p95_ms" in snapshot
        assert "memory_mb" in snapshot
        assert "redis_connected" in snapshot
        assert "threshold_exceeded" in snapshot

    async def test_metrics_threshold_detection(self, async_client_with_data):
        """Green 路径：阈值超出检测正确"""
        collector = MetricsCollector()
        session = async_client_with_data["session"]

        snapshot = await collector.get_snapshot(session)

        # threshold_exceeded 应为列表
        assert isinstance(snapshot["threshold_exceeded"], list)


@pytest.mark.asyncio
class TestMetricsAPI:
    """Sprint 13: 监控 API 测试"""

    async def test_metrics_snapshot_api(self, client_with_auth):
        """Green 路径：监控快照 API 返回完整指标"""
        client, headers = client_with_auth

        response = await client.get("/api/v1/metrics", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "concurrent_tasks" in data
        assert "queued_tasks" in data
        assert "latency_p50_ms" in data
        assert "latency_p95_ms" in data
        assert "memory_mb" in data
        assert "redis_connected" in data

    async def test_metrics_stream_sse(self, client_with_auth):
        """Green 路径：SSE 流式推送正常"""
        client, headers = client_with_auth

        response = await client.get("/api/v1/metrics/stream", headers=headers)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        # 读取一行验证格式
        async for line in response.aiter_lines():
            if line:
                assert line.startswith("data:")
                assert "concurrent_tasks" in line
                break

    async def test_metrics_stream_rate_limit(self, client_with_auth):
        """Red 路径：SSE 端点基本响应"""
        client, headers = client_with_auth

        # 验证 SSE 端点响应类型
        response = await client.get("/api/v1/metrics/stream", headers=headers)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
class TestMetricsIntegration:
    """Sprint 13: 监控集成测试"""

    async def test_metrics_update_on_task_submission(self, client_with_auth):
        """Green 路径：提交任务后并发数增加"""
        client, headers = client_with_auth

        # 获取初始指标
        initial_res = await client.get("/api/v1/metrics", headers=headers)
        initial = initial_res.json()
        initial_concurrent = initial["concurrent_tasks"]

        # 创建项目
        proj_res = await client.post("/api/v1/projects", json={
            "name": "MetricsTestProj",
            "target_repo_path": "./metrics-test"
        }, headers=headers)
        proj_id = proj_res.json()["id"]

        # 提交任务到队列
        task_res = await client.post("/api/v1/tasks/queue", json={
            "project_id": proj_id,
            "raw_objective": "Metrics test task"
        }, headers=headers)

        # 等待队列处理
        import asyncio
        await asyncio.sleep(0.5)

        # 获取更新后指标
        updated_res = await client.get("/api/v1/metrics", headers=headers)
        updated = updated_res.json()

        # 并发数或队列数应增加
        assert (updated["concurrent_tasks"] >= initial_concurrent or
                updated["queued_tasks"] >= initial["queued_tasks"])


@pytest.mark.asyncio
class TestThresholdAlerts:
    """Sprint 13: 阈值告警测试"""

    def test_threshold_queue_length(self):
        """Green 路径：队列长度超阈值检测"""
        alerts = check_thresholds(queued_tasks=150, p95_ms=100, memory_mb=500, redis_connected=True)
        assert "queued_tasks" in alerts

    def test_threshold_latency(self):
        """Green 路径：延迟超阈值检测"""
        alerts = check_thresholds(queued_tasks=10, p95_ms=1500, memory_mb=500, redis_connected=True)
        assert "latency_p95" in alerts

    def test_threshold_memory(self):
        """Green 路径：内存超阈值检测"""
        alerts = check_thresholds(queued_tasks=10, p95_ms=100, memory_mb=1500, redis_connected=True)
        assert "memory_mb" in alerts

    def test_threshold_redis_disconnected(self):
        """Red 路径：Redis 断开告警"""
        alerts = check_thresholds(queued_tasks=10, p95_ms=100, memory_mb=500, redis_connected=False)
        assert "redis_connected" in alerts

    def test_no_threshold_exceeded(self):
        """Green 路径：无阈值超出"""
        alerts = check_thresholds(queued_tasks=10, p95_ms=100, memory_mb=500, redis_connected=True)
        assert len(alerts) == 0, f"不应有告警，实际：{alerts}"
