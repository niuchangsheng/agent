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

@app.get("/api/v1/tasks")
async def list_tasks(session: AsyncSession = Depends(get_db_session)):
    result = await session.exec(select(Task).order_by(Task.id.desc()).limit(10))
    return result.all()

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
    result = await session.exec(select(Trace).where(Trace.task_id == task_id))
    traces = result.all()
    
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

@app.post("/api/v1/tasks/{task_id}/generate-adr")
async def generate_task_adr(task_id: int, session: AsyncSession = Depends(get_db_session)):
    import os
    from app.models import Trace, Task, Adr

    task_result = await session.exec(select(Task).where(Task.id == task_id))
    task = task_result.one_or_none()
    if not task:
        return JSONResponse(status_code=404, content={"detail": "Task missing"})

    trace_result = await session.exec(select(Trace).where(Trace.task_id == task_id))
    traces = trace_result.all()
    
    # We only care about passes for generating "learned" solution ADR, 
    # but could include failures as anti-patterns in a real LLM. For mock, we simply aggregate applied_patch.
    success_patches = [t.applied_patch for t in traces if t.is_success and t.applied_patch]
    
    markdown_content = f"""# ADR Auto-Generated for Task {task_id}
    
## Context
System encountered a task: {task.raw_objective}.
Below are successful patches applied during dynamic sandbox tracing:

{"".join(f"- {p}\\n" for p in success_patches)}
    """
    
    adr = Adr(
        task_id=task_id, 
        brief_title=f"Decisions for {task_id}", 
        generated_markdown_payload=markdown_content
    )
    session.add(adr)
    await session.commit()
    await session.refresh(adr)
    
    # Physical File Down sync
    storage_path = os.getenv("ADR_STORAGE_PATH", "../../artifacts/decisions")
    os.makedirs(storage_path, exist_ok=True)
    file_path = os.path.join(storage_path, f"ADR-{adr.id:03d}.md")
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    return adr.model_dump()

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
