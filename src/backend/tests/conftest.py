import pytest
import asyncio
from app.database import engine
from sqlmodel import SQLModel, select
from httpx import ASGITransport, AsyncClient
from app.main import app, global_queue
from app.queue import InMemoryQueue
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Task, AuditLog
from datetime import datetime, timezone, timedelta


@pytest.fixture(scope="function", autouse=True)
async def dispose_engine():
    """Ensure engine connections are cleaned up. Function scope to align with default loop."""
    yield
    # We don't necessarily need to dispose the whole engine after every test,
    # but the warning comes from unclosed connections.
    # The async generator in database.py handles session cleanup now.


@pytest.fixture(autouse=True)
async def setup_test_db():
    """每个测试前设置数据库状态"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # 清理数据（可选）


@pytest.fixture
async def async_client_with_data():
    """提供带测试数据的异步客户端和 session"""
    from app.main import global_queue as gq
    import app.main

    # 确保队列已初始化
    if app.main.global_queue is None:
        app.main.global_queue = InMemoryQueue(max_concurrent=2)

    async with AsyncSession(engine) as session:
        # 清理旧数据
        from app.models import Task, AuditLog, Project
        result = await session.exec(select(Task))
        for task in result.all():
            await session.delete(task)
        result = await session.exec(select(AuditLog))
        for log in result.all():
            await session.delete(log)
        result = await session.exec(select(Project))
        for proj in result.all():
            await session.delete(proj)
        await session.commit()

        # 创建测试项目
        project = Project(name="MetricsTest", target_repo_path="./metrics-test")
        session.add(project)
        await session.commit()
        await session.refresh(project)

        # 获取项目 ID（在 session 关闭前）
        project_id = project.id

        # 创建测试任务：1 个 RUNNING, 2 个 QUEUED
        task1 = Task(project_id=project_id, raw_objective="Running task", status="RUNNING")
        task2 = Task(project_id=project_id, raw_objective="Queued task 1", status="QUEUED")
        task3 = Task(project_id=project_id, raw_objective="Queued task 2", status="QUEUED")
        session.add_all([task1, task2, task3])

        # 创建测试审计日志（用于延迟测试）
        base_time = datetime.now(timezone.utc)
        for i in range(10):
            log = AuditLog(
                action="POST",
                resource="/api/v1/tasks",
                duration_ms=50 + i * 10,  # 50, 60, 70, ..., 140
                timestamp=base_time - timedelta(minutes=i)
            )
            session.add(log)

        await session.commit()

        # 返回 session 和项目 ID
        yield {"session": session, "project_id": project_id}


@pytest.fixture
async def client_with_auth():
    """提供带认证的 HTTP 客户端"""
    from app.main import app, global_queue as gq

    # 确保队列已初始化
    if global_queue is None:
        from app.queue import InMemoryQueue
        from app import main
        main.global_queue = InMemoryQueue(max_concurrent=2)

    # 创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 创建 API Key
        key_res = await client.post("/api/v1/auth/api-keys", json={
            "name": "MetricsTestKey",
            "permissions": ["read", "write"]
        })
        api_key = key_res.json()["key"]
        headers = {"X-API-Key": api_key}

        yield client, headers
