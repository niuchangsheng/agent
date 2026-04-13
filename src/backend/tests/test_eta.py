"""
Sprint 12: ETA 预测测试套件
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.eta import ETACalculator


class TestETACalculator:
    """Sprint 12: ETA 计算器测试"""

    def test_eta_calculator_initialization(self):
        """Green 路径：ETA 计算器初始化"""
        calculator = ETACalculator()
        assert calculator.get_eta() is None, "初始状态应返回 None"
        assert calculator.get_remaining_seconds() is None, "初始状态应返回 None"

    def test_eta_calculator_insufficient_samples(self):
        """Red 路径：样本不足时返回 None"""
        calculator = ETACalculator()

        # 添加 1 个样本
        calculator.add_progress_sample(10, datetime.now(timezone.utc))
        assert calculator.get_eta() is None, "1 个样本应返回 None"

        # 添加 2 个样本
        calculator.add_progress_sample(20, datetime.now(timezone.utc))
        assert calculator.get_eta() is None, "2 个样本应返回 None"

        # 添加第 3 个样本
        calculator.add_progress_sample(30, datetime.now(timezone.utc))
        assert calculator.get_eta() is not None, "3 个样本应返回 ETA"

    def test_eta_calculator_moving_average(self):
        """Green 路径：移动平均计算正确"""
        calculator = ETACalculator()

        now = datetime.now(timezone.utc)

        # 模拟进度更新：每 10 秒增加 10%
        # 0% @ 0s, 10% @ 10s, 20% @ 20s, 30% @ 30s
        base_time = now - timedelta(seconds=30)
        calculator.add_progress_sample(0, base_time)
        calculator.add_progress_sample(10, base_time + timedelta(seconds=10))
        calculator.add_progress_sample(20, base_time + timedelta(seconds=20))
        calculator.add_progress_sample(30, base_time + timedelta(seconds=30))

        # 当前 30% 进度，平均每 10 秒走 10%
        # 剩余 70% 应该需要约 70 秒
        remaining = calculator.get_remaining_seconds()
        assert remaining is not None, "应返回剩余时间"
        assert 60 <= remaining <= 80, f"剩余时间应在 60-80 秒之间，实际：{remaining}"

    def test_eta_calculator_task_complete(self):
        """Green 路径：任务完成时 ETA 归零"""
        calculator = ETACalculator()
        calculator.add_progress_sample(0, datetime.now(timezone.utc))
        calculator.add_progress_sample(50, datetime.now(timezone.utc))
        calculator.add_progress_sample(100, datetime.now(timezone.utc))

        # 100% 进度时，剩余时间应为 0
        remaining = calculator.get_remaining_seconds()
        assert remaining == 0, "100% 进度时剩余时间应为 0"

    def test_eta_calculator_nonlinear_progress(self):
        """Red 路径：非线性进度处理"""
        calculator = ETACalculator()

        now = datetime.now(timezone.utc)

        # 模拟非线性进度：前慢后快
        # 0% @ 0s, 10% @ 20s (慢), 30% @ 30s (快), 50% @ 40s (快)
        base_time = now - timedelta(seconds=40)
        calculator.add_progress_sample(0, base_time)
        calculator.add_progress_sample(10, base_time + timedelta(seconds=20))
        calculator.add_progress_sample(30, base_time + timedelta(seconds=30))
        calculator.add_progress_sample(50, base_time + timedelta(seconds=40))

        # 移动平均应平滑瞬时波动
        remaining = calculator.get_remaining_seconds()
        assert remaining is not None, "应返回剩余时间"
        assert remaining > 0, "剩余时间应大于 0"

    def test_eta_calculator_reset(self):
        """Red 路径：重置计算器"""
        calculator = ETACalculator()

        # 添加足够样本
        now = datetime.now(timezone.utc)
        for i in range(5):
            calculator.add_progress_sample(i * 20, now + timedelta(seconds=i * 10))

        assert calculator.get_eta() is not None, "应有 ETA"

        # 重置
        calculator.reset()
        assert calculator.get_eta() is None, "重置后应返回 None"

    def test_eta_estimated_completion_time(self):
        """Green 路径：预计完成时间计算"""
        calculator = ETACalculator()

        now = datetime.now(timezone.utc)

        # 模拟稳定进度
        base_time = now - timedelta(seconds=20)
        calculator.add_progress_sample(0, base_time)
        calculator.add_progress_sample(25, base_time + timedelta(seconds=10))
        calculator.add_progress_sample(50, base_time + timedelta(seconds=20))

        # 50% 进度用了 20 秒，剩余 50% 应该需要 20 秒
        completion_time = calculator.get_estimated_completion_time()
        assert completion_time is not None, "应返回预计完成时间"

        # 完成时间应该是现在 + 约 20 秒
        expected_completion = now + timedelta(seconds=20)
        time_diff = abs((completion_time - expected_completion).total_seconds())
        assert time_diff < 10, f"完成时间应在预期范围内，差异：{time_diff}秒"


@pytest.mark.asyncio
class TestTaskETAIntegration:
    """Sprint 12: 任务 ETA 集成测试"""

    async def test_task_api_returns_eta_fields(self):
        """Green 路径：任务 API 返回 ETA 字段"""
        from app.database import engine
        from sqlmodel import SQLModel
        from httpx import ASGITransport, AsyncClient
        from app.main import app, global_queue
        from app.queue import InMemoryQueue

        # 初始化全局队列（测试环境）
        if global_queue is None:
            from app import main
            main.global_queue = InMemoryQueue(max_concurrent=2)

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "ETATestKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 创建项目
            project_res = await client.post("/api/v1/projects", json={
                "name": "ETATestProject",
                "target_repo_path": "./eta-test"
            }, headers={"X-API-Key": api_key})
            project_id = project_res.json()["id"]

            # 创建队列任务
            task_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": project_id,
                "raw_objective": "ETA test task",
                "priority": 5
            }, headers={"X-API-Key": api_key})
            task_id = task_res.json()["id"]

            # 获取任务详情
            task_detail_res = await client.get(f"/api/v1/tasks/{task_id}")
            task = task_detail_res.json()

            # 验证 ETA 字段存在
            assert "estimated_remaining_seconds" in task or "eta" in task or "estimated_completion_at" in task, "任务详情应包含 ETA 字段"


@pytest.mark.asyncio
class TestPriorityQueue:
    """Sprint 12: 优先级队列测试"""

    async def test_priority_queue_ordering(self):
        """Red 路径：高优先级先出队"""
        from app.queue import InMemoryQueue

        queue = InMemoryQueue(max_concurrent=2)

        # 添加不同优先级的任务
        await queue.enqueue(1, 1, "Low priority task", priority=1)
        await queue.enqueue(2, 1, "High priority task", priority=10)
        await queue.enqueue(3, 1, "Medium priority task", priority=5)

        #  dequeue 应该返回高优先级任务
        task1 = await queue.dequeue()
        assert task1.task_id == 2, f"应首先返回高优先级任务，实际：{task1.task_id}"

        task2 = await queue.dequeue()
        assert task2.task_id == 3, f"应返回中优先级任务，实际：{task2.task_id}"

        task3 = await queue.dequeue()
        assert task3.task_id == 1, f"应返回低优先级任务，实际：{task3.task_id}"

    async def test_priority_fifo_same_priority(self):
        """Green 路径：同优先级 FIFO 顺序"""
        from app.queue import InMemoryQueue

        queue = InMemoryQueue(max_concurrent=2)

        # 添加相同优先级的任务
        await queue.enqueue(1, 1, "First task", priority=5)
        await queue.enqueue(2, 1, "Second task", priority=5)
        await queue.enqueue(3, 1, "Third task", priority=5)

        # 应该按 FIFO 顺序返回
        task1 = await queue.dequeue()
        assert task1.task_id == 1, "应首先返回第一个任务"

        task2 = await queue.dequeue()
        assert task2.task_id == 2, "应返回第二个任务"

        task3 = await queue.dequeue()
        assert task3.task_id == 3, "应返回第三个任务"

    async def test_priority_preemption(self):
        """Red 路径：高优先级插队"""
        from app.queue import InMemoryQueue

        queue = InMemoryQueue(max_concurrent=1)

        # 添加低优先级任务
        await queue.enqueue(1, 1, "Low priority task", priority=1)

        # 模拟 Worker 占用
        await queue.start_task(1, "worker-1")

        # 添加高优先级任务
        await queue.enqueue(2, 1, "High priority task", priority=10)

        # 完成当前任务
        await queue.complete_task(1)

        # 下一个 dequeue 应该返回高优先级任务
        task = await queue.dequeue()
        assert task is not None, "应有任务可 dequeue"
        assert task.task_id == 2, f"应返回高优先级任务，实际：{task.task_id}"

    async def test_priority_update(self):
        """Green 路径：任务优先级可更新"""
        from app.queue import InMemoryQueue

        queue = InMemoryQueue(max_concurrent=2)

        # 添加低优先级任务
        await queue.enqueue(1, 1, "Low priority task", priority=1)
        await queue.enqueue(2, 1, "Medium priority task", priority=5)

        # 更新任务 1 的优先级为高
        updated = await queue.update_priority(1, 10)
        assert updated is True, "优先级应更新成功"

        # 高优先级应先出队
        task1 = await queue.dequeue()
        assert task1.task_id == 1, "更新后高优先级应先出队"


@pytest.mark.asyncio
class TestPriorityRegression:
    """Sprint 9: 优先级队列回归测试"""

    async def test_queue_basic_functionality(self):
        """回归测试：队列基础功能正常"""
        from app.queue import InMemoryQueue

        queue = InMemoryQueue(max_concurrent=2)

        # 基础入队
        position = await queue.enqueue(1, 1, "Test task", priority=5)
        assert position == 1, "队列位置应为 1"

        # 出队
        task = await queue.dequeue()
        assert task is not None, "应有任务可出队"
        assert task.task_id == 1, "任务 ID 应正确"

    async def test_task_progress_update(self):
        """回归测试：任务进度更新正常"""
        from app.queue import InMemoryQueue

        queue = InMemoryQueue(max_concurrent=2)

        # 入队并启动
        await queue.enqueue(1, 1, "Test task", priority=5)
        await queue.start_task(1, "worker-1")

        # 更新进度
        updated = await queue.update_progress(1, 50, "Half done")
        assert updated is True, "进度应更新成功"
