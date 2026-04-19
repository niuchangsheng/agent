"""Sprint 19 整修: API 层 tenant_id 过滤安全测试
测试 Tenant B 无法通过 API 端点获取 Tenant A 的数据
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import engine
from app.main import app
from app.models import Tenant, Project, Task, APIKey, Trace
from datetime import datetime, timezone
import hashlib
import secrets


@pytest.fixture
async def setup_api_tenant_isolation():
    """API 层多租户隔离测试环境"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # 清理所有数据
        for model in [Tenant, APIKey, Project, Task, Trace]:
            result = await session.exec(select(model))
            for item in result.all():
                await session.delete(item)
        await session.commit()

        # 创建两个租户
        tenant_a = Tenant(name="Tenant A", slug="tenant-a")
        tenant_b = Tenant(name="Tenant B", slug="tenant-b")
        session.add_all([tenant_a, tenant_b])
        await session.commit()
        await session.refresh(tenant_a)
        await session.refresh(tenant_b)

        tenant_a_id = tenant_a.id
        tenant_b_id = tenant_b.id

        # 创建 Tenant A 的 API Key (真实 key hash)
        key_a_raw = secrets.token_urlsafe(32)
        key_a_hash = hashlib.sha256(key_a_raw.encode()).hexdigest()
        key_a = APIKey(
            name="Key A",
            key_hash=key_a_hash,
            permissions=["read", "write"],
            tenant_id=tenant_a_id
        )
        session.add(key_a)
        await session.commit()
        await session.refresh(key_a)
        key_a_id = key_a.id

        # 创建 Tenant B 的 API Key (真实 key hash)
        key_b_raw = secrets.token_urlsafe(32)
        key_b_hash = hashlib.sha256(key_b_raw.encode()).hexdigest()
        key_b = APIKey(
            name="Key B",
            key_hash=key_b_hash,
            permissions=["read", "write"],
            tenant_id=tenant_b_id
        )
        session.add(key_b)
        await session.commit()
        await session.refresh(key_b)
        key_b_id = key_b.id

        # 创建 Tenant A 的项目
        project_a = Project(
            name="Project A",
            target_repo_path="./project-a",
            tenant_id=tenant_a_id
        )
        session.add(project_a)
        await session.commit()
        await session.refresh(project_a)
        project_a_id = project_a.id

        # 创建 Tenant B 的项目
        project_b = Project(
            name="Project B",
            target_repo_path="./project-b",
            tenant_id=tenant_b_id
        )
        session.add(project_b)
        await session.commit()
        await session.refresh(project_b)
        project_b_id = project_b.id

        # 创建 Tenant A 的任务
        task_a = Task(
            project_id=project_a_id,
            raw_objective="Task A Objective",
            status="COMPLETED",
            tenant_id=tenant_a_id
        )
        session.add(task_a)
        await session.commit()
        await session.refresh(task_a)
        task_a_id = task_a.id

        # 创建 Tenant B 的任务
        task_b = Task(
            project_id=project_b_id,
            raw_objective="Task B Objective",
            status="RUNNING",
            tenant_id=tenant_b_id
        )
        session.add(task_b)
        await session.commit()
        await session.refresh(task_b)
        task_b_id = task_b.id

        # 创建 Tenant A 的 Trace
        trace_a = Trace(
            task_id=task_a_id,
            agent_role="generator",
            tenant_id=tenant_a_id,
            perception_log="Tenant A perception"
        )
        session.add(trace_a)
        await session.commit()
        await session.refresh(trace_a)
        trace_a_id = trace_a.id

        yield {
            "tenant_a_id": tenant_a_id,
            "tenant_b_id": tenant_b_id,
            "key_a_id": key_a_id,
            "key_b_id": key_b_id,
            "key_a_raw": key_a_raw,
            "key_b_raw": key_b_raw,
            "project_a_id": project_a_id,
            "project_b_id": project_b_id,
            "task_a_id": task_a_id,
            "task_b_id": task_b_id,
            "trace_a_id": trace_a_id
        }


# API-001: Tenant B 无法看到 Tenant A 的项目
@pytest.mark.asyncio
async def test_api_list_projects_tenant_filter(setup_api_tenant_isolation):
    """Tenant B 请求 /api/v1/projects 应仅返回 tenant_id=2 的项目"""
    setup_data = setup_api_tenant_isolation
    key_b_raw = setup_data["key_b_raw"]
    tenant_b_id = setup_data["tenant_b_id"]
    project_a_id = setup_data["project_a_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/projects",
            headers={"X-API-Key": key_b_raw}
        )

        assert response.status_code == 200
        projects = response.json()

        # Tenant B 不应看到 Tenant A 的项目
        project_ids = [p["id"] for p in projects]
        assert project_a_id not in project_ids

        # 所有返回项目的 tenant_id 应为 Tenant B
        for p in projects:
            assert p["tenant_id"] == tenant_b_id


# API-002: Tenant B 无法看到 Tenant A 的任务
@pytest.mark.asyncio
async def test_api_list_tasks_tenant_filter(setup_api_tenant_isolation):
    """Tenant B 请求 /api/v1/tasks 应仅返回 tenant_id=2 的任务"""
    setup_data = setup_api_tenant_isolation
    key_b_raw = setup_data["key_b_raw"]
    tenant_b_id = setup_data["tenant_b_id"]
    task_a_id = setup_data["task_a_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/tasks",
            headers={"X-API-Key": key_b_raw}
        )

        assert response.status_code == 200
        tasks = response.json()

        # Tenant B 不应看到 Tenant A 的任务
        task_ids = [t["id"] for t in tasks]
        assert task_a_id not in task_ids

        # 所有返回任务的 tenant_id 应为 Tenant B
        for t in tasks:
            assert t["tenant_id"] == tenant_b_id


# API-003: Tenant B 无法获取 Tenant A 任务的 DAG Tree
@pytest.mark.asyncio
async def test_api_dag_tree_cross_tenant_denied(setup_api_tenant_isolation):
    """Tenant B 请求 /api/v1/tasks/{task_a_id}/dag-tree 应返回空或 403"""
    setup_data = setup_api_tenant_isolation
    key_b_raw = setup_data["key_b_raw"]
    task_a_id = setup_data["task_a_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(
            f"/api/v1/tasks/{task_a_id}/dag-tree",
            headers={"X-API-Key": key_b_raw}
        )

        # 应返回 403 Forbidden 或空数组
        if response.status_code == 200:
            # 如果返回 200，内容必须为空数组
            assert response.json() == []
        else:
            # 应返回 403 或 404
            assert response.status_code in [403, 404]


# API-004: Tenant B 无法为 Tenant A 任务生成 ADR
@pytest.mark.asyncio
async def test_api_generate_adr_cross_tenant_denied(setup_api_tenant_isolation):
    """Tenant B 请求 /api/v1/tasks/{task_a_id}/generate-adr 应返回 403"""
    setup_data = setup_api_tenant_isolation
    key_b_raw = setup_data["key_b_raw"]
    task_a_id = setup_data["task_a_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/v1/tasks/{task_a_id}/generate-adr",
            headers={"X-API-Key": key_b_raw}
        )

        # 应返回 403 Forbidden 或 404
        assert response.status_code in [403, 404]


# API-005: Tenant B 的 containers 仅显示 Tenant B 的任务
@pytest.mark.asyncio
async def test_api_containers_tenant_filter(setup_api_tenant_isolation):
    """Tenant B 请求 /api/v1/containers 应仅显示 Tenant B 的 RUNNING 任务"""
    setup_data = setup_api_tenant_isolation
    key_b_raw = setup_data["key_b_raw"]
    task_a_id = setup_data["task_a_id"]
    task_b_id = setup_data["task_b_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/containers",
            headers={"X-API-Key": key_b_raw}
        )

        assert response.status_code == 200
        containers = response.json()

        # Tenant B 不应看到 Tenant A 的任务容器
        task_ids = [c["task_id"] for c in containers]
        assert task_a_id not in task_ids

        # Tenant B 应看到自己的 RUNNING 任务
        # (task_b_id 在测试环境中 status=RUNNING)
        # 注意: 容器端点仅返回 RUNNING 状态任务


# API-006: Tenant B 无法获取 Tenant A 任务的日志
@pytest.mark.asyncio
async def test_api_task_logs_cross_tenant_denied(setup_api_tenant_isolation):
    """Tenant B 请求 /api/v1/tasks/{task_a_id}/logs 应返回 403"""
    setup_data = setup_api_tenant_isolation
    key_b_raw = setup_data["key_b_raw"]
    task_a_id = setup_data["task_a_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.get(
            f"/api/v1/tasks/{task_a_id}/logs",
            headers={"X-API-Key": key_b_raw}
        )

        # 应返回 403 Forbidden 或 404
        assert response.status_code in [403, 404]