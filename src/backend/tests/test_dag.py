import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel, select

from app.main import app
from app.database import engine
from app.models import Project, Task, Trace, APIKey, Tenant
import secrets
import hashlib


@pytest.fixture
async def setup_dag_test():
    """Setup test data with API key for authenticated endpoints"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Clean existing data
        for model in [Tenant, APIKey, Project, Task, Trace]:
            result = await session.exec(select(model))
            for item in result.all():
                await session.delete(item)
        await session.commit()

        # Create default tenant
        tenant = Tenant(name="Test Tenant", slug="test-tenant")
        session.add(tenant)
        await session.commit()
        await session.refresh(tenant)
        tenant_id = tenant.id

        # Create API Key
        key_raw = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key_raw.encode()).hexdigest()
        api_key = APIKey(
            name="Test Key",
            key_hash=key_hash,
            permissions=["read", "write"],
            tenant_id=tenant_id
        )
        session.add(api_key)
        await session.commit()

        # Create Project and Task
        proj = Project(name="TestProj", target_repo_path="/d", tenant_id=tenant_id)
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        p_id = proj.id

        task = Task(project_id=p_id, raw_objective="Fix DAG", tenant_id=tenant_id)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        t_id = task.id

        yield {
            "key_raw": key_raw,
            "tenant_id": tenant_id,
            "project_id": p_id,
            "task_id": t_id
        }


@pytest.mark.asyncio
async def test_dag_tree_assembly(setup_dag_test):
    """Test DAG tree assembly with authentication"""
    setup_data = setup_dag_test
    key_raw = setup_data["key_raw"]
    tenant_id = setup_data["tenant_id"]
    t_id = setup_data["task_id"]

    async with AsyncSession(engine) as session:
        # Create Root Trace
        t_root = Trace(task_id=t_id, agent_role="generator", is_success=True, tenant_id=tenant_id)
        session.add(t_root)
        await session.commit()
        await session.refresh(t_root)
        r_id = t_root.id

        # Create Branch 1 (Failed attempt)
        t_fail = Trace(task_id=t_id, parent_trace_id=r_id, agent_role="generator", is_success=False, tenant_id=tenant_id)
        session.add(t_fail)

        # Create Branch 2 (Valid pathway)
        t_pass = Trace(task_id=t_id, parent_trace_id=r_id, agent_role="generator", is_success=True, tenant_id=tenant_id)
        session.add(t_pass)
        await session.commit()
        await session.refresh(t_pass)
        p_sub_id = t_pass.id

        # Create leaf under Branch 2
        t_leaf = Trace(task_id=t_id, parent_trace_id=p_sub_id, agent_role="evaluator", is_success=True, tenant_id=tenant_id)
        session.add(t_leaf)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Fetch the DAG tree with API key
        response = await client.get(
            f"/api/v1/tasks/{t_id}/dag-tree",
            headers={"X-API-Key": key_raw}
        )
        assert response.status_code == 200

        DAG = response.json()
        assert len(DAG) == 1  # only one root
        root_node = DAG[0]
        assert root_node["id"] == r_id
        # Root has two children
        assert len(root_node["children"]) == 2

        # Find the successful branch
        pass_branch = next(c for c in root_node["children"] if c["is_success"])
        assert len(pass_branch["children"]) == 1 # Has leaf


@pytest.mark.asyncio
async def test_dag_empty_task_returns_empty_array(setup_dag_test):
    """Test empty task returns empty array with authentication"""
    setup_data = setup_dag_test
    key_raw = setup_data["key_raw"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/tasks/999/dag-tree",
            headers={"X-API-Key": key_raw}
        )
        assert response.status_code == 200
        assert response.json() == []
