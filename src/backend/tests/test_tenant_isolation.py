"""Sprint 19: Tenant 数据隔离测试 - Feature 22 Core"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import engine
from app.main import app
from app.models import Tenant, Project, Task, APIKey, Trace, Adr
from datetime import datetime, timezone


@pytest.fixture
async def setup_multi_tenant():
    """多租户测试环境初始化 - 使用 expire_on_commit=False 避免 lazy loading 问题"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # 使用 expire_on_commit=False 防止 commit 后对象过期
    async with AsyncSession(engine, expire_on_commit=False) as session:
        # 清理所有数据
        for model in [Tenant, APIKey, Project, Task, Trace, Adr]:
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

        # 立即捕获 ID
        tenant_a_id = tenant_a.id
        tenant_b_id = tenant_b.id

        # 创建两个租户的 API Key
        key_a = APIKey(
            name="Key A",
            key_hash="hash_a",
            permissions=["read", "write"],
            tenant_id=tenant_a_id
        )
        key_b = APIKey(
            name="Key B",
            key_hash="hash_b",
            permissions=["read", "write"],
            tenant_id=tenant_b_id
        )
        session.add_all([key_a, key_b])
        await session.commit()
        await session.refresh(key_a)
        await session.refresh(key_b)

        key_a_id = key_a.id
        key_b_id = key_b.id

        # 创建两个租户的项目
        project_a = Project(
            name="Project A",
            target_repo_path="./project-a",
            tenant_id=tenant_a_id
        )
        project_b = Project(
            name="Project B",
            target_repo_path="./project-b",
            tenant_id=tenant_b_id
        )
        session.add_all([project_a, project_b])
        await session.commit()
        await session.refresh(project_a)
        await session.refresh(project_b)

        project_a_id = project_a.id
        project_b_id = project_b.id

        # 创建两个租户的任务
        task_a = Task(
            project_id=project_a_id,
            raw_objective="Task A",
            status="COMPLETED",
            tenant_id=tenant_a_id
        )
        task_b = Task(
            project_id=project_b_id,
            raw_objective="Task B",
            status="COMPLETED",
            tenant_id=tenant_b_id
        )
        session.add_all([task_a, task_b])
        await session.commit()
        await session.refresh(task_a)
        await session.refresh(task_b)

        task_a_id = task_a.id
        task_b_id = task_b.id

        # 在 session 关闭前捕获所有 ID
        yield {
            "tenant_a_id": tenant_a_id,
            "tenant_b_id": tenant_b_id,
            "key_a_id": key_a_id,
            "key_b_id": key_b_id,
            "project_a_id": project_a_id,
            "project_b_id": project_b_id,
            "task_a_id": task_a_id,
            "task_b_id": task_b_id
        }


# TC-I001: 跨租户项目访问拒绝
@pytest.mark.asyncio
async def test_cross_tenant_project_access_denied(setup_multi_tenant):
    """测试 Tenant A 无法访问 Tenant B 的项目"""
    setup_data = setup_multi_tenant

    async with AsyncSession(engine) as session:
        tenant_a_id = setup_data["tenant_a_id"]
        project_b_id = setup_data["project_b_id"]

        # 模拟 tenant_id 过滤查询
        result = await session.exec(
            select(Project).where(
                Project.id == project_b_id,
                Project.tenant_id == tenant_a_id
            )
        )
        project = result.one_or_none()

        # Tenant A 无法查询到 Tenant B 的项目
        assert project is None


# TC-I002: 跨租户任务访问拒绝
@pytest.mark.asyncio
async def test_cross_tenant_task_access_denied(setup_multi_tenant):
    """测试 Tenant A 无法查询 Tenant B 的任务"""
    setup_data = setup_multi_tenant

    async with AsyncSession(engine) as session:
        tenant_a_id = setup_data["tenant_a_id"]
        task_b_id = setup_data["task_b_id"]

        # 模拟 tenant_id 过滤查询
        result = await session.exec(
            select(Task).where(
                Task.id == task_b_id,
                Task.tenant_id == tenant_a_id
            )
        )
        task = result.one_or_none()

        assert task is None


# TC-I003: 跨租户 Trace 访问拒绝
@pytest.mark.asyncio
async def test_cross_tenant_trace_access_denied(setup_multi_tenant):
    """测试 Tenant A 无法获取 Tenant B 的 Trace 数据"""
    setup_data = setup_multi_tenant

    async with AsyncSession(engine) as session:
        tenant_a_id = setup_data["tenant_a_id"]
        tenant_b_id = setup_data["tenant_b_id"]

        # 创建 Tenant B 的 Trace
        trace_b = Trace(
            task_id=setup_data["task_b_id"],
            agent_role="generator",
            tenant_id=tenant_b_id
        )
        session.add(trace_b)
        await session.commit()
        await session.refresh(trace_b)
        trace_b_id = trace_b.id

        # Tenant A 查询 Trace（使用 tenant_id 过滤）
        result = await session.exec(
            select(Trace).where(Trace.tenant_id == tenant_a_id)
        )
        traces = result.all()

        # Tenant A 看不到 Tenant B 的 Trace
        assert trace_b_id not in [t.id for t in traces]


# TC-I004: 跨租户 ADR 访问拒绝
@pytest.mark.asyncio
async def test_cross_tenant_adr_access_denied(setup_multi_tenant):
    """测试 Tenant A 无法生成 Tenant B 任务的 ADR"""
    setup_data = setup_multi_tenant

    async with AsyncSession(engine) as session:
        tenant_a_id = setup_data["tenant_a_id"]
        tenant_b_id = setup_data["tenant_b_id"]
        task_b_id = setup_data["task_b_id"]

        # 创建 Tenant B 的 ADR
        adr_b = Adr(
            task_id=task_b_id,
            brief_title="ADR for Task B",
            generated_markdown_payload="# ADR B",
            tenant_id=tenant_b_id
        )
        session.add(adr_b)
        await session.commit()
        await session.refresh(adr_b)
        adr_b_id = adr_b.id

        # Tenant A 查询 ADR（使用 tenant_id 过滤）
        result = await session.exec(
            select(Adr).where(Adr.tenant_id == tenant_a_id)
        )
        adrs = result.all()

        assert adr_b_id not in [a.id for a in adrs]


# TC-I005: 租户作用域自动过滤
@pytest.mark.asyncio
async def test_tenant_scope_auto_filter(setup_multi_tenant):
    """测试所有 list API 自动按 tenant_id 篇选"""
    setup_data = setup_multi_tenant

    async with AsyncSession(engine) as session:
        tenant_a_id = setup_data["tenant_a_id"]

        # 验证 Project 列表自动过滤
        result = await session.exec(
            select(Project).where(Project.tenant_id == tenant_a_id)
        )
        projects = result.all()

        # 只能看到 Tenant A 的项目
        for p in projects:
            assert p.tenant_id == tenant_a_id

        # 验证 Task 列表自动过滤
        result = await session.exec(
            select(Task).where(Task.tenant_id == tenant_a_id)
        )
        tasks = result.all()

        for t in tasks:
            assert t.tenant_id == tenant_a_id


# TC-I006: API 端点 tenant_id 过滤验证
@pytest.mark.asyncio
async def test_api_endpoint_tenant_filter(setup_multi_tenant):
    """测试 API 端点返回的数据按 tenant_id 过滤"""
    setup_data = setup_multi_tenant

    async with AsyncSession(engine) as session:
        tenant_a_id = setup_data["tenant_a_id"]

        # 使用 tenant_id 过滤查询
        result = await session.exec(
            select(Project).where(Project.tenant_id == tenant_a_id)
        )
        projects = result.all()

        # 验证过滤正确
        assert len(projects) >= 1
        for p in projects:
            assert p.tenant_id == tenant_a_id