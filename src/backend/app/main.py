import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select

from app.database import engine, get_db_session
from app.models import Project, Task
from pydantic import BaseModel
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

class ProjectCreate(BaseModel):
    name: str
    target_repo_path: str

class TaskCreate(BaseModel):
    project_id: int
    raw_objective: str

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    await engine.dispose()

app = FastAPI(title="SECA API", lifespan=lifespan)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "active"}

@app.post("/api/v1/projects")
async def create_project(proj: ProjectCreate, session: AsyncSession = Depends(get_db_session)):
    db_proj = Project(name=proj.name, target_repo_path=proj.target_repo_path)
    session.add(db_proj)
    await session.commit()
    await session.refresh(db_proj)
    return db_proj

@app.post("/api/v1/tasks")
async def create_task(task_in: TaskCreate, session: AsyncSession = Depends(get_db_session)):
    db_task = Task(project_id=task_in.project_id, raw_objective=task_in.raw_objective)
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)
    return db_task

@app.get("/api/v1/tasks/{task_id}/stream")
async def stream_task_events(task_id: int):
    async def event_generator():
        # Yield an initial heartbeat or status payload
        yield f"data: {{\"type\": \"status\", \"content\": \"Connected to stream for {task_id}\"}}\n\n"
        # Simulate agent execution flow for testing
        await asyncio.sleep(0.1)
        yield f"data: {{\"type\": \"perception\", \"content\": \"Started analysis...\"}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/v1/tasks/{task_id}/dag-tree")
async def get_task_dag_tree(task_id: int, session: AsyncSession = Depends(get_db_session)):
    from app.models import Trace
    result = await session.execute(select(Trace).where(Trace.task_id == task_id))
    traces = result.scalars().all()
    
    if not traces:
        return JSONResponse(content=[], status_code=200)

    # Convert to dicts for nested injection
    nodes = {t.id: {"id": t.id, "parent_trace_id": t.parent_trace_id, "agent_role": t.agent_role, "is_success": t.is_success, "children": []} for t in traces}
    
    roots = []
    for node_id, node in nodes.items():
        parent_id = node.get("parent_trace_id")
        if parent_id is None:
            roots.append(node)
        else:
            if parent_id in nodes:
                nodes[parent_id]["children"].append(node)
            else:
                # Fallback if parent is somehow dead or missing, treat as root to avoid dropping
                roots.append(node)
                
    return JSONResponse(content=roots, status_code=200)

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
