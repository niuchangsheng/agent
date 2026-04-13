import pytest
from httpx import AsyncClient
from app.models import Project, Task
from app.main import app, global_queue
from app.queue import InMemoryQueue
import asyncio


@pytest.fixture(autouse=True)
async def reset_queue():
    """每个测试前重置队列状态"""
    # 确保队列已初始化
    if global_queue is None:
        from app.main import global_queue as gq
        # 在测试中直接创建内存队列
        import app.main
        app.main.global_queue = InMemoryQueue(max_concurrent=2)
    elif hasattr(global_queue, 'queued'):
        global_queue.queued = []
        global_queue.running = {}
    yield


async def get_api_key_header(client):
    """获取带写权限的 API Key 请求头"""
    key_res = await client.post("/api/v1/auth/api-keys", json={
        "name": "TestKey",
        "permissions": ["read", "write"]
    })
    api_key = key_res.json()["key"]
    return {"X-API-Key": api_key}


@pytest.mark.asyncio
class TestTaskQueue:
    """Sprint 7: 异步任务队列测试套件"""

    async def test_queue_task_submission(self):
        """Green 路径：任务提交到队列"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "QueueTestProj",
                "target_repo_path": "./queue-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            # 提交任务到队列
            queue_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": proj_id,
                "raw_objective": "Test queue task"
            }, headers=headers)
            assert queue_res.status_code == 200
            result = queue_res.json()
            assert result["status"] == "QUEUED"
            assert "queue_position" in result

    async def test_queue_concurrency_limit(self):
        """Green 路径：2 并发限制下 3 任务正确调度"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "ConcurrencyTest",
                "target_repo_path": "./concurrency-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            # 提交 3 个任务
            task_ids = []
            for i in range(3):
                queue_res = await client.post("/api/v1/tasks/queue", json={
                    "project_id": proj_id,
                    "raw_objective": f"Task {i}"
                }, headers=headers)
                task_ids.append(queue_res.json()["id"])

            # 检查队列状态
            queue_status = await client.get("/api/v1/tasks/queue")
            assert queue_status.status_code == 200
            queue_data = queue_status.json()

            running_count = len(queue_data.get("running", []))
            queued_count = len(queue_data.get("queued", []))

            assert running_count <= 2, "并发任务数不应超过 2"
            assert running_count + queued_count == 3, "总任务数应为 3"

    async def test_queue_task_progress_update(self):
        """Green 路径：任务进度更新"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目并提交任务
            proj_res = await client.post("/api/v1/projects", json={
                "name": "ProgressTest",
                "target_repo_path": "./progress-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            queue_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": proj_id,
                "raw_objective": "Progress tracking task"
            }, headers=headers)
            task_id = queue_res.json()["id"]

            # 更新进度
            progress_res = await client.put(f"/api/v1/tasks/{task_id}/progress", json={
                "progress_percent": 50,
                "status_message": "Processing..."
            }, headers=headers)
            assert progress_res.status_code == 200
            result = progress_res.json()
            assert result["progress_percent"] == 50
            assert result["status_message"] == "Processing..."

    async def test_queue_task_completion(self):
        """Green 路径：任务完成后释放槽位"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目并提交 2 个任务
            proj_res = await client.post("/api/v1/projects", json={
                "name": "CompletionTest",
                "target_repo_path": "./completion-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            task_ids = []
            for i in range(2):
                queue_res = await client.post("/api/v1/tasks/queue", json={
                    "project_id": proj_id,
                    "raw_objective": f"Completion task {i}"
                }, headers=headers)
                task_ids.append(queue_res.json()["id"])

            # 完成第一个任务
            complete_res = await client.post(f"/api/v1/tasks/{task_ids[0]}/complete", json={
                "result": "Success"
            }, headers=headers)
            assert complete_res.status_code == 200

            # 验证队列状态
            queue_status = await client.get("/api/v1/tasks/queue")
            assert queue_status.status_code == 200

    async def test_queue_cancel_task(self):
        """Green 路径：取消队列中任务"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目并提交任务
            proj_res = await client.post("/api/v1/projects", json={
                "name": "CancelTest",
                "target_repo_path": "./cancel-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            queue_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": proj_id,
                "raw_objective": "Task to cancel"
            }, headers=headers)
            task_id = queue_res.json()["id"]

            # 取消任务
            cancel_res = await client.delete(f"/api/v1/tasks/queue/{task_id}", headers=headers)
            assert cancel_res.status_code == 200
            result = cancel_res.json()
            assert result["status"] == "CANCELLED"

    async def test_queue_task_not_found_returns_404(self):
        """Red 路径：任务不存在返回 404"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 获取不存在的任务进度 (读操作无需认证)
            progress_res = await client.get("/api/v1/tasks/99999/progress")
            assert progress_res.status_code == 404

    async def test_queue_cancel_non_existent_task(self):
        """Red 路径：取消不存在任务失败"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)
            # 取消不存在的任务
            cancel_res = await client.delete("/api/v1/tasks/queue/99999", headers=headers)
            assert cancel_res.status_code == 404

    async def test_queue_invalid_progress_value(self):
        """Red 路径：无效进度值验证"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目并提交任务
            proj_res = await client.post("/api/v1/projects", json={
                "name": "InvalidProgressTest",
                "target_repo_path": "./invalid-progress-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            queue_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": proj_id,
                "raw_objective": "Invalid progress task"
            }, headers=headers)
            task_id = queue_res.json()["id"]

            # 进度 < 0
            progress_res = await client.put(f"/api/v1/tasks/{task_id}/progress", json={
                "progress_percent": -10
            }, headers=headers)
            assert progress_res.status_code == 422

            # 进度 > 100
            progress_res = await client.put(f"/api/v1/tasks/{task_id}/progress", json={
                "progress_percent": 150
            }, headers=headers)
            assert progress_res.status_code == 422

    async def test_queue_worker_crash_recovery(self):
        """集成测试：Worker 崩溃后任务重新入队"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目并提交任务
            proj_res = await client.post("/api/v1/projects", json={
                "name": "RecoveryTest",
                "target_repo_path": "./recovery-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            queue_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": proj_id,
                "raw_objective": "Recovery task"
            }, headers=headers)
            task_id = queue_res.json()["id"]

            # 模拟 Worker 崩溃
            crash_res = await client.post(f"/api/v1/tasks/{task_id}/worker-crash", json={
                "error": "Simulated worker crash"
            }, headers=headers)
            assert crash_res.status_code == 200

            # 验证任务重新入队
            queue_status = await client.get("/api/v1/tasks/queue")
            assert queue_status.status_code == 200
            queue_data = queue_status.json()

            all_tasks = queue_data.get("queued", []) + queue_data.get("running", [])
            task_found = any(t["task_id"] == task_id for t in all_tasks)
            assert task_found, "崩溃后任务应重新入队"

    async def test_queue_progress_real_time(self):
        """集成测试：进度实时更新验证"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await get_api_key_header(client)

            # 创建项目并提交任务
            proj_res = await client.post("/api/v1/projects", json={
                "name": "RealTimeProgressTest",
                "target_repo_path": "./realtime-progress-test"
            }, headers=headers)
            proj_id = proj_res.json()["id"]

            queue_res = await client.post("/api/v1/tasks/queue", json={
                "project_id": proj_id,
                "raw_objective": "Real-time progress task"
            }, headers=headers)
            task_id = queue_res.json()["id"]

            # 多次更新进度
            for percent in [25, 50, 75, 100]:
                progress_res = await client.put(f"/api/v1/tasks/{task_id}/progress", json={
                    "progress_percent": percent,
                    "status_message": f"Progress {percent}%"
                }, headers=headers)
                assert progress_res.status_code == 200

                # 立即获取进度验证
                get_res = await client.get(f"/api/v1/tasks/{task_id}/progress")
                assert get_res.status_code == 200
                result = get_res.json()
                assert result["progress_percent"] == percent
