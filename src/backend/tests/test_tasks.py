import pytest
from httpx import AsyncClient
from sqlmodel import select
from app.main import app
from app.database import engine
from app.models import Task, Trace

@pytest.mark.asyncio
async def test_create_task_and_ensure_persistence():
    # Insert dummy project row first to avoid FK error
    from app.models import Project
    async with engine.begin() as conn:
        from sqlmodel import SQLModel
        await conn.run_sync(SQLModel.metadata.create_all)
    
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a new project for FK mapping
        proj_res = await client.post("/api/v1/projects", json={"name": "TestProj", "target_repo_path": "./test"})
        assert proj_res.status_code == 200
        proj_id = proj_res.json()["id"]

        # Request to launch a task
        response = await client.post("/api/v1/tasks", json={"project_id": proj_id, "raw_objective": "Fix bug"})
        assert response.status_code == 200
        task_data = response.json()
        assert task_data["status"] == "PENDING"
        task_id = task_data["id"]

    # Verify task was inserted in DB
    from app.database import get_db_session
    async with engine.connect() as conn:
        from sqlmodel.ext.asyncio.session import AsyncSession
        async with AsyncSession(engine) as session:
            db_task = await session.get(Task, task_id)
            assert db_task is not None
            assert db_task.raw_objective == "Fix bug"
