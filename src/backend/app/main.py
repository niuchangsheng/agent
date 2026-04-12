import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select
from typing import Optional, Dict
from datetime import datetime, timezone

from app.database import engine, get_db_session
from app.models import Project, Task, ProjectConfig
from app.task_queue import global_queue
from pydantic import BaseModel, Field
from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

class ProjectCreate(BaseModel):
    name: str
    target_repo_path: str

class TaskCreate(BaseModel):
    project_id: int
    raw_objective: str

class ProjectConfigCreate(BaseModel):
    sandbox_timeout_seconds: int = Field(ge=1, le=60, default=30)
    max_memory_mb: int = Field(ge=128, le=2048, default=512)
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict)

class TaskQueueCreate(BaseModel):
    project_id: int
    raw_objective: str

class TaskProgressUpdate(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    status_message: str = ""

class TaskComplete(BaseModel):
    result: str

class ProjectConfigUpdate(BaseModel):
    sandbox_timeout_seconds: Optional[int] = Field(None, ge=1, le=60)
    max_memory_mb: Optional[int] = Field(None, ge=128, le=2048)
    environment_variables: Optional[Dict[str, str]] = None

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

@app.post("/api/v1/projects/{project_id}/config")
async def create_project_config(
    project_id: int,
    config_in: ProjectConfigCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """创建项目配置"""
    # 验证项目存在
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    # 检查配置是否已存在
    result = await session.exec(select(ProjectConfig).where(ProjectConfig.project_id == project_id))
    existing = result.one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Config already exists, use PUT to update")

    db_config = ProjectConfig(
        project_id=project_id,
        sandbox_timeout_seconds=config_in.sandbox_timeout_seconds,
        max_memory_mb=config_in.max_memory_mb,
        environment_variables=config_in.environment_variables
    )
    session.add(db_config)
    await session.commit()
    await session.refresh(db_config)
    return db_config

@app.get("/api/v1/projects/{project_id}/config")
async def get_project_config(
    project_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """获取项目配置"""
    result = await session.exec(select(ProjectConfig).where(ProjectConfig.project_id == project_id))
    config = result.one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return config

@app.put("/api/v1/projects/{project_id}/config")
async def update_project_config(
    project_id: int,
    config_in: ProjectConfigUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """更新项目配置"""
    result = await session.exec(select(ProjectConfig).where(ProjectConfig.project_id == project_id))
    config = result.one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    # 验证项目存在
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    update_data = config_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    config.updated_at = datetime.now(timezone.utc)
    session.add(config)
    await session.commit()
    await session.refresh(config)
    return config

# ============== Sprint 7: Task Queue Endpoints ==============

from app.task_queue import global_queue
import uuid

@app.post("/api/v1/tasks/queue")
async def queue_task(
    task_in: TaskQueueCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """提交任务到队列"""
    # 验证项目存在
    project = await session.get(Project, task_in.project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    # 创建任务
    db_task = Task(
        project_id=task_in.project_id,
        raw_objective=task_in.raw_objective,
        status="QUEUED"
    )
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)

    # 加入队列
    position = await global_queue.enqueue(db_task.id, task_in.project_id, task_in.raw_objective)
    db_task.queue_position = position
    await session.commit()

    return db_task

@app.get("/api/v1/tasks/queue")
async def get_queue_status():
    """获取队列状态"""
    return await global_queue.get_status()

@app.delete("/api/v1/tasks/queue/{task_id}")
async def cancel_queued_task(
    task_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """取消队列中的任务"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    cancelled = await global_queue.cancel_task(task_id)
    if cancelled:
        task.status = "CANCELLED"
        await session.commit()
        return {"status": "CANCELLED", "task_id": task_id}
    else:
        raise HTTPException(status_code=400, detail="Task cannot be cancelled")

@app.get("/api/v1/tasks/{task_id}/progress")
async def get_task_progress(
    task_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """获取任务进度"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task_id,
        "progress_percent": task.progress_percent,
        "status_message": task.status_message,
        "status": task.status
    }

@app.put("/api/v1/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: int,
    progress_in: TaskProgressUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """更新任务进度"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.progress_percent = progress_in.progress_percent
    task.status_message = progress_in.status_message
    if progress_in.progress_percent == 100:
        task.status = "COMPLETED"
        task.completed_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(task)
    return task

@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    complete_in: TaskComplete,
    session: AsyncSession = Depends(get_db_session)
):
    """标记任务为完成"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "COMPLETED"
    task.completed_at = datetime.now(timezone.utc)
    task.progress_percent = 100
    task.status_message = complete_in.result

    await global_queue.complete_task(task_id)
    await session.commit()

    # 触发队列调度：尝试启动下一个任务
    await process_queue(session)

    return task

@app.post("/api/v1/tasks/{task_id}/worker-crash")
async def simulate_worker_crash(
    task_id: int,
    crash_in: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """模拟 Worker 崩溃 - 任务重新入队"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 重新入队
    await global_queue.requeue_on_crash(task_id, task.project_id, task.raw_objective)
    task.status = "QUEUED"
    task.queue_position = len(global_queue.queued)

    await session.commit()
    return {"status": "REQUEUED", "task_id": task_id}

async def process_queue(session: AsyncSession):
    """处理队列：尝试启动等待的任务"""
    while True:
        queued_task = await global_queue.dequeue()
        if not queued_task:
            break
        # 启动任务
        worker_id = str(uuid.uuid4())[:8]
        await global_queue.start_task(queued_task.task_id, worker_id)
        # 更新数据库
        task = await session.get(Task, queued_task.task_id)
        if task:
            task.status = "RUNNING"
            task.worker_id = worker_id
            task.started_at = datetime.now(timezone.utc)
            task.queue_position = None
            await session.commit()

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
