import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

from app.main import app
from app.database import engine
from app.models import Project, Task, Trace

@pytest.mark.asyncio
async def test_dag_tree_assembly():
    # Setup test data
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Create Dummy Project and Task
        proj = Project(name="TestProj", target_repo_path="/d")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        p_id = proj.id

        task = Task(project_id=p_id, raw_objective="Fix DAG")
        session.add(task)
        await session.commit()
        await session.refresh(task)
        t_id = task.id

        # Create Root Trace
        t_root = Trace(task_id=t_id, agent_role="generator", is_success=True)
        session.add(t_root)
        await session.commit()
        await session.refresh(t_root)
        r_id = t_root.id

        # Create Branch 1 (Failed attempt)
        t_fail = Trace(task_id=t_id, parent_trace_id=r_id, agent_role="generator", is_success=False)
        session.add(t_fail)
        
        # Create Branch 2 (Valid pathway)
        t_pass = Trace(task_id=t_id, parent_trace_id=r_id, agent_role="generator", is_success=True)
        session.add(t_pass)
        await session.commit()
        await session.refresh(t_pass)
        p_sub_id = t_pass.id

        # Create leaf under Branch 2
        t_leaf = Trace(task_id=t_id, parent_trace_id=p_sub_id, agent_role="evaluator", is_success=True)
        session.add(t_leaf)
        await session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Fetch the DAG tree
        response = await client.get(f"/api/v1/tasks/{t_id}/dag-tree")
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
async def test_dag_empty_task_returns_empty_array():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/tasks/999/dag-tree")
        assert response.status_code == 200
        assert response.json() == []
