import pytest
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
import os

from app.main import app
from app.database import engine
from app.models import Project, Task, Trace, Adr

@pytest.mark.asyncio
async def test_adr_generation_flow(tmp_path):
    # Setup test env and point physical writer path to tmp_path
    os.environ["ADR_STORAGE_PATH"] = str(tmp_path)
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        proj = Project(name="Proj", target_repo_path="/d")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        p_id = proj.id

        task = Task(project_id=p_id, raw_objective="Fix memory leak")
        session.add(task)
        await session.commit()
        await session.refresh(task)
        t_id = task.id

        t_pass = Trace(task_id=t_id, agent_role="generator", is_success=True, applied_patch="Use a weakref dict instead of list.")
        session.add(t_pass)
        await session.commit()

    # Trigger Generation
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(f"/api/v1/tasks/{t_id}/generate-adr")
        assert response.status_code == 200
        data = response.json()
        assert "weakref" in data["generated_markdown_payload"]
        adr_id = data["id"]
        assert adr_id is not None
        
        # Verify physical file existence
        expected_file = tmp_path / f"ADR-{adr_id:03d}.md"
        assert expected_file.exists()
        
        content = expected_file.read_text()
        assert "weakref" in content
