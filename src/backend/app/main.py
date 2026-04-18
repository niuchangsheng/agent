import asyncio
import os
import logging
import time
from typing import AsyncGenerator, List, Optional, Dict
from fastapi import FastAPI, Depends, Request, Header, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlmodel import SQLModel, select
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import engine, get_db_session
from app.models import Project, Task, ProjectConfig, APIKey, AuditLog, DockerConfig, Tenant
from app.auth import require_write_key, require_read_key, generate_api_key, hash_api_key
from app.eta import update_task_eta, get_eta_calculator
from app.metrics import MetricsCollector, check_thresholds
from app.tenant import init_default_tenant, get_quota_usage, check_quota_limit
# Sprint 9: 导入新队列模块
from app.queue import create_queue, BaseQueue

logger = logging.getLogger(__name__)

# 全局队列实例（Sprint 9）
global_queue: BaseQueue = None

def get_ip_address(request: Request) -> str:
    """获取请求 IP 地址（支持 X-Forwarded-For）"""
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # X-Forwarded-For 可能包含多个 IP，取第一个
        return x_forwarded_for.split(",")[0].strip()
    # 降级使用 client.host
    if request.client:
        return request.client.host
    return "unknown"

async def create_audit_log(
    session: AsyncSession,
    action: str,
    resource: str,
    api_key_id: Optional[int],
    ip_address: str,
    user_agent: str,
    duration_ms: int,
    details: Optional[Dict] = None
):
    """异步创建审计日志"""
    audit_log = AuditLog(
        api_key_id=api_key_id,
        action=action,
        resource=resource,
        ip_address=ip_address,
        user_agent=user_agent,
        duration_ms=duration_ms,
        details=details or {}
    )
    session.add(audit_log)
    await session.commit()

class ProjectCreate(BaseModel):
    name: str
    target_repo_path: str

class TaskCreate(BaseModel):
    project_id: int
    raw_objective: str
    priority: int = 0

class ProjectConfigCreate(BaseModel):
    sandbox_timeout_seconds: int = Field(ge=1, le=60, default=30)
    max_memory_mb: int = Field(ge=128, le=2048, default=512)
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict)

class TaskQueueCreate(BaseModel):
    project_id: int
    raw_objective: str
    priority: int = Field(default=0, ge=0, le=10)  # Sprint 9: 优先级

class TaskProgressUpdate(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    status_message: str = ""

class TaskComplete(BaseModel):
    result: str

class ProjectConfigUpdate(BaseModel):
    sandbox_timeout_seconds: Optional[int] = Field(None, ge=1, le=60)
    max_memory_mb: Optional[int] = Field(None, ge=128, le=2048)
    environment_variables: Optional[Dict[str, str]] = None

class APIKeyCreate(BaseModel):
    name: str
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    tenant_id: Optional[int] = Field(default=None)  # Sprint 19: 租户绑定

class APIKeyResponse(BaseModel):
    id: int
    name: str
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_active: bool

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global global_queue

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Sprint 19: 初始化默认租户
    async with AsyncSession(engine) as session:
        await init_default_tenant(session)

    # Sprint 9: 初始化队列（支持 Redis 降级）
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        from app.queue import RedisQueue
        global_queue = RedisQueue(redis_url=redis_url, max_concurrent=2)
        connected = await global_queue.connect()
        if connected:
            # 从持久化恢复未完成任务
            await global_queue.recover_from_persistence()
            logger.info("Redis queue initialized with recovery")
        else:
            # 降级到内存队列
            from app.queue import InMemoryQueue
            global_queue = InMemoryQueue(max_concurrent=2)
            logger.warning("Falling back to in-memory queue")
    else:
        # 无 Redis 配置，使用内存队列
        from app.queue import InMemoryQueue
        global_queue = InMemoryQueue(max_concurrent=2)
        logger.info("In-memory queue initialized")

    yield

    # 清理
    if global_queue and hasattr(global_queue, 'close'):
        await global_queue.close()

    await engine.dispose()

app = FastAPI(title="SECA API", lifespan=lifespan)

# CORS 配置 - 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器 - 确保所有错误返回 JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

# Audit Log Middleware - captures IP, User-Agent, duration for write operations
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    start_time = time.time()

    # 捕获请求信息
    ip_address = get_ip_address(request)
    user_agent = request.headers.get("User-Agent", "")

    # 执行请求
    response = await call_next(request)

    # 计算耗时
    duration_ms = int((time.time() - start_time) * 1000)

    # 只对写操作记录审计日志
    write_methods = {"POST", "PUT", "DELETE", "PATCH"}
    if request.method in write_methods:
        # 从请求状态中获取 API Key ID（如果有）
        api_key_id = getattr(request.state, "api_key_id", None)

        # 创建审计日志（使用后台任务）
        asyncio.create_task(
            _save_audit_log(
                api_key_id=api_key_id,
                ip_address=ip_address,
                user_agent=user_agent,
                duration_ms=duration_ms,
                method=request.method,
                path=str(request.url.path)
            )
        )

    return response


async def _save_audit_log(
    api_key_id: Optional[int],
    ip_address: str,
    user_agent: str,
    duration_ms: int,
    method: str,
    path: str
):
    """后台任务：保存审计日志"""
    async with engine.begin() as conn:
        audit_log = AuditLog(
            api_key_id=api_key_id,
            action=method,
            resource=path,
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms,
            details={"method": method, "path": path}
        )
        session = AsyncSession(bind=engine, expire_on_commit=False)
        async with session:
            session.add(audit_log)
            await session.commit()

@app.get("/api/v1/health")
async def health_check():
    return {"status": "active"}

@app.get("/api/v1/projects")
async def list_projects(session: AsyncSession = Depends(get_db_session)):
    """列出所有项目"""
    result = await session.exec(select(Project).order_by(Project.id.desc()))
    return result.all()

@app.post("/api/v1/projects")
async def create_project(
    proj: ProjectCreate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """创建项目 - 需要写权限"""
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
async def create_task(
    task_in: TaskCreate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """创建任务 - 需要写权限，自动加入队列"""
    db_task = Task(project_id=task_in.project_id, raw_objective=task_in.raw_objective, priority=task_in.priority)
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)

    # 自动加入队列
    if global_queue:
        try:
            await global_queue.enqueue(db_task.id, task_in.project_id, task_in.raw_objective, task_in.priority)
        except Exception as e:
            logger.warning(f"Failed to enqueue task {db_task.id}: {e}")

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
async def generate_task_adr(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """生成 ADR - 需要写权限"""
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
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """创建项目配置 - 需要写权限"""
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
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """更新项目配置 - 需要写权限"""
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

# ============== Sprint 7/9: Task Queue Endpoints ==============

import uuid

@app.post("/api/v1/tasks/queue")
async def queue_task(
    task_in: TaskQueueCreate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """提交任务到队列 - 需要写权限"""
    # 验证项目存在
    project = await session.get(Project, task_in.project_id)
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    # 创建任务
    db_task = Task(
        project_id=task_in.project_id,
        raw_objective=task_in.raw_objective,
        status="QUEUED",
        priority=task_in.priority
    )
    session.add(db_task)
    await session.commit()
    await session.refresh(db_task)

    # 加入队列（支持优先级）
    position = await global_queue.enqueue(db_task.id, task_in.project_id, task_in.raw_objective, task_in.priority)
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
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """取消队列中的任务 - 需要写权限"""
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

@app.get("/api/v1/tasks/{task_id}")
async def get_task_detail(
    task_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """获取任务详情（包含 ETA）"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 计算 ETA（如果数据库中没有或需要更新）
    calculator = get_eta_calculator(task_id)
    calculator.add_progress_sample(task.progress_percent, task.updated_at or task.created_at)
    remaining_seconds = calculator.get_remaining_seconds()
    eta_string = calculator.get_eta()

    return {
        "id": task.id,
        "project_id": task.project_id,
        "raw_objective": task.raw_objective,
        "status": task.status,
        "progress_percent": task.progress_percent,
        "status_message": task.status_message,
        "priority": task.priority,
        "queue_position": task.queue_position,
        "worker_id": task.worker_id,
        "started_at": task.started_at.isoformat() if task.started_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "estimated_remaining_seconds": task.estimated_remaining_seconds or remaining_seconds,
        "estimated_completion_at": task.estimated_completion_at.isoformat() if task.estimated_completion_at else None,
        "eta": eta_string or (task.estimated_remaining_seconds and f"剩余约 {task.estimated_remaining_seconds} 秒")
    }

@app.put("/api/v1/tasks/{task_id}/priority")
async def update_task_priority(
    task_id: int,
    priority: int = Query(ge=0, le=10),
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """更新任务优先级 - 需要写权限"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 更新数据库中的优先级
    task.priority = priority
    await session.commit()

    # 更新队列中的优先级
    try:
        await global_queue.update_priority(task_id, priority)
    except Exception as e:
        logger.warning(f"Failed to update priority in queue: {e}")

    await session.refresh(task)
    return task

@app.put("/api/v1/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: int,
    progress_in: TaskProgressUpdate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """更新任务进度 - 需要写权限"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.progress_percent = progress_in.progress_percent
    task.status_message = progress_in.status_message
    if progress_in.progress_percent == 100:
        task.status = "COMPLETED"
        task.completed_at = datetime.now(timezone.utc)

    # 更新 ETA
    remaining_seconds, eta_string = update_task_eta(task_id, progress_in.progress_percent)
    task.estimated_remaining_seconds = remaining_seconds
    if remaining_seconds is not None:
        task.estimated_completion_at = datetime.now(timezone.utc) + timedelta(seconds=remaining_seconds)

    await session.commit()
    await session.refresh(task)
    return task

@app.post("/api/v1/tasks/{task_id}/complete")
async def complete_task(
    task_id: int,
    complete_in: TaskComplete,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """标记任务为完成 - 需要写权限"""
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
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """模拟 Worker 崩溃 - 需要写权限"""
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

# ============== Sprint 8: Auth & Audit Endpoints ==============

from app.auth import hash_api_key, generate_api_key, require_write_key, require_read_key

@app.post("/api/v1/auth/api-keys")
async def create_api_key(
    key_in: APIKeyCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """创建 API Key"""
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)

    # Sprint 19: 处理租户绑定
    tenant_id = key_in.tenant_id
    if tenant_id is None:
        # 自动绑定默认租户
        result = await session.exec(select(Tenant).where(Tenant.slug == "default"))
        default_tenant = result.one_or_none()
        if default_tenant:
            tenant_id = default_tenant.id

    db_key = APIKey(
        name=key_in.name,
        key_hash=key_hash,
        permissions=key_in.permissions,
        expires_at=key_in.expires_at,
        tenant_id=tenant_id
    )
    session.add(db_key)
    await session.commit()
    await session.refresh(db_key)

    return {
        "id": db_key.id,
        "key": raw_key,  # 仅在创建时返回一次
        "name": db_key.name,
        "permissions": db_key.permissions,
        "tenant_id": db_key.tenant_id,  # Sprint 19: 返回租户 ID
        "created_at": db_key.created_at,
        "expires_at": db_key.expires_at
    }

@app.get("/api/v1/auth/api-keys")
async def list_api_keys(session: AsyncSession = Depends(get_db_session)):
    """列出所有活跃的 API Key"""
    result = await session.exec(select(APIKey).where(APIKey.is_active == True).order_by(APIKey.id.desc()))
    keys = result.all()
    return [
        {
            "id": k.id,
            "name": k.name,
            "permissions": k.permissions,
            "created_at": k.created_at,
            "expires_at": k.expires_at,
            "is_active": k.is_active
        }
        for k in keys
    ]

@app.delete("/api/v1/auth/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """删除 API Key"""
    key = await session.get(APIKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found")

    key.is_active = False
    await session.commit()
    return {"status": "deleted", "id": key_id}

@app.get("/api/v1/audit-logs")
async def list_audit_logs(
    session: AsyncSession = Depends(get_db_session),
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20
):
    """列出审计日志（支持筛选和分页）"""
    from datetime import datetime

    # 构建查询条件
    query = select(AuditLog)

    # 时间范围筛选
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            query = query.where(AuditLog.timestamp >= start_dt)
        except ValueError:
            pass

    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            query = query.where(AuditLog.timestamp <= end_dt)
        except ValueError:
            pass

    # 操作类型筛选
    if action:
        query = query.where(AuditLog.action == action.upper())

    # 用户 ID 筛选
    if user_id:
        query = query.where(AuditLog.api_key_id == user_id)

    # 按时间倒序
    query = query.order_by(AuditLog.timestamp.desc())

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await session.exec(query)
    logs = result.all()

    return [
        {
            "id": l.id,
            "api_key_id": l.api_key_id,
            "action": l.action,
            "resource": l.resource,
            "timestamp": l.timestamp.isoformat(),
            "ip_address": l.ip_address,
            "user_agent": l.user_agent,
            "duration_ms": l.duration_ms,
            "details": l.details
        }
        for l in logs
    ]


# ============== Sprint 13: System Monitoring Endpoints ==============

class SystemMetricsResponse(BaseModel):
    """系统监控指标响应模型"""
    concurrent_tasks: int
    queued_tasks: int
    latency_p50_ms: float
    latency_p95_ms: float
    memory_mb: float
    redis_connected: bool
    threshold_exceeded: list[str]


@app.get("/api/v1/metrics")
async def get_metrics(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_read_key)
):
    """获取系统监控指标快照"""
    collector = MetricsCollector()
    snapshot = await collector.get_snapshot(session)
    return snapshot


@app.get("/api/v1/metrics/stream")
async def stream_metrics(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_read_key)
):
    """SSE 流式推送系统监控指标（10 秒更新频率）"""
    collector = MetricsCollector()

    # 关键修复：在 session 关闭前先获取 snapshot 数据
    # 避免在生成器 yield 时使用已释放的 session
    snapshot = await collector.get_snapshot(session)

    async def event_generator():
        yield f"data: {snapshot}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ============== Sprint 17: Docker Operations Endpoints ==============

class DockerConfigResponse(BaseModel):
    """Docker 配置响应模型"""
    id: int
    memory_limit_mb: int
    cpu_limit: float
    timeout_seconds: int
    max_concurrent_containers: int


class DockerConfigCreate(BaseModel):
    """Docker 配置创建模型"""
    memory_limit_mb: int = Field(default=512, ge=64, le=4096)
    cpu_limit: float = Field(default=1.0, ge=0.5, le=4.0)
    timeout_seconds: int = Field(default=60, ge=10, le=300)
    max_concurrent_containers: int = Field(default=3, ge=1, le=10)


class DockerConfigUpdate(BaseModel):
    """Docker 配置更新模型"""
    memory_limit_mb: Optional[int] = Field(None, ge=64, le=4096)
    cpu_limit: Optional[float] = Field(None, ge=0.5, le=4.0)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=300)
    max_concurrent_containers: Optional[int] = Field(None, ge=1, le=10)


@app.get("/api/v1/docker-config")
async def get_docker_config(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取 Docker 沙箱配置"""
    result = await session.exec(select(DockerConfig).order_by(DockerConfig.id.desc()).limit(1))
    config = result.one_or_none()

    if not config:
        # 返回默认配置
        return {
            "memory_limit_mb": 512,
            "cpu_limit": 1.0,
            "timeout_seconds": 60,
            "max_concurrent_containers": 3
        }

    return {
        "id": config.id,
        "memory_limit_mb": config.memory_limit_mb,
        "cpu_limit": config.cpu_limit,
        "timeout_seconds": config.timeout_seconds,
        "max_concurrent_containers": config.max_concurrent_containers
    }


@app.put("/api/v1/docker-config")
async def update_docker_config(
    config_in: DockerConfigUpdate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """更新 Docker 沙箱配置"""
    result = await session.exec(select(DockerConfig).order_by(DockerConfig.id.desc()).limit(1))
    config = result.one_or_none()

    update_data = config_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    if not config:
        # 创建新配置
        create_data = config_in.model_dump()
        db_config = DockerConfig(**create_data)
        session.add(db_config)
    else:
        # 更新现有配置
        for key, value in update_data.items():
            setattr(config, key, value)
        config.updated_at = datetime.now(timezone.utc)
        session.add(config)
        db_config = config

    await session.commit()
    await session.refresh(db_config)

    return {
        "id": db_config.id,
        "memory_limit_mb": db_config.memory_limit_mb,
        "cpu_limit": db_config.cpu_limit,
        "timeout_seconds": db_config.timeout_seconds,
        "max_concurrent_containers": db_config.max_concurrent_containers
    }


class ContainerStats(BaseModel):
    """容器统计响应模型"""
    container_id: Optional[str]
    task_id: Optional[int]
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    network_rx_bytes: int = 0
    network_tx_bytes: int = 0
    running_time_seconds: Optional[int]
    alert: bool = False


@app.get("/api/v1/containers")
async def list_containers(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取运行中容器列表"""
    # 查询 RUNNING 状态的任务
    result = await session.exec(
        select(Task).where(Task.status == "RUNNING").order_by(Task.id.desc())
    )
    tasks = result.all()

    containers = []
    for task in tasks:
        # 计算运行时长
        running_time = None
        if task.started_at:
            running_time = int((datetime.now(timezone.utc) - task.started_at).total_seconds())

        # 模拟容器统计（实际应从 Docker API 获取）
        # 这里返回 mock 数据用于测试
        container = {
            "container_id": f"container-{task.id}",
            "task_id": task.id,
            "task_objective": task.raw_objective,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "network_rx_bytes": 0,
            "network_tx_bytes": 0,
            "running_time_seconds": running_time,
            "alert": False
        }
        containers.append(container)

    return containers


@app.get("/api/v1/containers/{container_id}/stats")
async def get_container_stats(
    container_id: str,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取单个容器资源统计"""
    # 从 container_id 解析 task_id
    if container_id.startswith("container-"):
        task_id = int(container_id.replace("container-", ""))
        task = await session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Container not found")

        running_time = None
        if task.started_at:
            running_time = int((datetime.now(timezone.utc) - task.started_at).total_seconds())

        return {
            "container_id": container_id,
            "task_id": task.id,
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "network_rx_bytes": 0,
            "network_tx_bytes": 0,
            "running_time_seconds": running_time,
            "alert": False
        }

    raise HTTPException(status_code=404, detail="Container not found")


@app.get("/api/v1/containers/history")
async def get_container_history(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取历史容器统计"""
    # 查询已完成或失败的任务
    result = await session.exec(
        select(Task)
        .where(Task.status.in_(["COMPLETED", "FAILED", "CANCELLED"]))
        .order_by(Task.completed_at.desc())
        .limit(20)
    )
    tasks = result.all()

    history = []
    for task in tasks:
        running_time = None
        if task.started_at and task.completed_at:
            running_time = int((task.completed_at - task.started_at).total_seconds())

        history.append({
            "container_id": f"container-{task.id}",
            "task_id": task.id,
            "task_objective": task.raw_objective,
            "status": task.status,
            "running_time_seconds": running_time,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        })

    return history


class LogResponse(BaseModel):
    """日志响应模型"""
    logs: str
    total_lines: int
    truncated: bool


@app.get("/api/v1/tasks/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    lines: int = Query(default=100, ge=1, le=1000),
    level: str = Query(default="ALL", regex="^(ALL|INFO|WARN|ERROR)$"),
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取任务日志"""
    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 获取任务的 Trace 日志
    from app.models import Trace
    result = await session.exec(
        select(Trace).where(Trace.task_id == task_id).order_by(Trace.id.desc())
    )
    traces = result.all()

    # 构建日志内容
    log_lines = []
    for trace in traces:
        if trace.perception_log:
            log_lines.append(f"[INFO] Perception: {trace.perception_log}")
        if trace.reasoning_log:
            log_lines.append(f"[INFO] Reasoning: {trace.reasoning_log}")
        if trace.applied_patch:
            log_lines.append(f"[INFO] Applied patch: {trace.applied_patch[:100]}...")

    # 按级别筛选（简化实现）
    if level != "ALL":
        filtered_lines = []
        for line in log_lines:
            if level in line:
                filtered_lines.append(line)
        log_lines = filtered_lines

    # 分页
    total_lines = len(log_lines)
    truncated = len(log_lines) > lines
    if truncated:
        log_lines = log_lines[:lines]

    return {
        "task_id": task_id,
        "logs": "\n".join(log_lines),
        "total_lines": total_lines,
        "truncated": truncated
    }


# ==================== Sprint 18 Feature 21: 镜像预拉取 ====================

class ImageConfigResponse(BaseModel):
    """镜像配置响应模型"""
    id: int
    name: str
    status: str
    last_pull_at: Optional[str] = None
    created_at: str
    updated_at: str


class ImageConfigCreate(BaseModel):
    """镜像配置创建模型"""
    name: str


@app.get("/api/v1/images")
async def get_image_configs(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取镜像配置列表"""
    from app.models import ImageConfig
    result = await session.exec(select(ImageConfig).order_by(ImageConfig.id))
    images = result.all()

    # 如果没有配置，返回默认镜像列表
    if not images:
        default_images = [
            ImageConfig(name="alpine:3.18", status="missing"),
            ImageConfig(name="python:3.11-slim", status="missing"),
            ImageConfig(name="node:20-alpine", status="missing"),
        ]
        for img in default_images:
            session.add(img)
        await session.commit()

        # 重新获取
        result = await session.exec(select(ImageConfig).order_by(ImageConfig.id))
        images = result.all()

    return [
        {
            "id": img.id,
            "name": img.name,
            "status": img.status,
            "last_pull_at": img.last_pull_at.isoformat() if img.last_pull_at else None,
            "created_at": img.created_at.isoformat(),
            "updated_at": img.updated_at.isoformat(),
        }
        for img in images
    ]


@app.post("/api/v1/images")
async def add_image_config(
    config: ImageConfigCreate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """添加镜像配置"""
    from app.models import ImageConfig
    from datetime import datetime, timezone

    # 检查是否已存在
    result = await session.exec(select(ImageConfig).where(ImageConfig.name == config.name))
    existing = result.one_or_none()

    if existing:
        return {
            "id": existing.id,
            "name": existing.name,
            "status": existing.status,
            "last_pull_at": existing.last_pull_at.isoformat() if existing.last_pull_at else None,
            "created_at": existing.created_at.isoformat(),
            "updated_at": existing.updated_at.isoformat(),
        }

    # 创建新配置
    new_image = ImageConfig(name=config.name, status="missing")
    session.add(new_image)
    await session.commit()
    await session.refresh(new_image)

    return {
        "id": new_image.id,
        "name": new_image.name,
        "status": new_image.status,
        "last_pull_at": None,
        "created_at": new_image.created_at.isoformat(),
        "updated_at": new_image.updated_at.isoformat(),
    }


@app.get("/api/v1/images/{image_name}/status")
async def get_image_status(
    image_name: str,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取镜像状态"""
    from app.models import ImageConfig

    # URL 编码的镜像名可能包含斜杠，需要解码
    import urllib.parse
    decoded_name = urllib.parse.unquote(image_name)

    result = await session.exec(select(ImageConfig).where(ImageConfig.name == decoded_name))
    image = result.one_or_none()

    if not image:
        return {"name": decoded_name, "status": "missing", "message": "Image not configured"}

    return {
        "name": image.name,
        "status": image.status,
        "last_pull_at": image.last_pull_at.isoformat() if image.last_pull_at else None,
    }


@app.post("/api/v1/images/{image_name}/pull")
async def trigger_image_pull(
    image_name: str,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """触发镜像拉取"""
    from app.models import ImageConfig
    from datetime import datetime, timezone
    import urllib.parse

    decoded_name = urllib.parse.unquote(image_name)

    result = await session.exec(select(ImageConfig).where(ImageConfig.name == decoded_name))
    image = result.one_or_none()

    if not image:
        # 自动创建配置
        image = ImageConfig(name=decoded_name, status="pulling")
        session.add(image)
    else:
        image.status = "pulling"
        image.updated_at = datetime.now(timezone.utc)

    await session.commit()

    # 标记为就绪（简化实现，实际应调用 Docker SDK）
    image.status = "ready"
    image.last_pull_at = datetime.now(timezone.utc)
    image.updated_at = datetime.now(timezone.utc)
    await session.commit()

    return {
        "name": image.name,
        "status": image.status,
        "message": "Pull triggered successfully",
    }


@app.delete("/api/v1/images/{image_id}")
async def delete_image_config(
    image_id: int,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """删除镜像配置"""
    from app.models import ImageConfig

    image = await session.get(ImageConfig, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image config not found")

    await session.delete(image)
    await session.commit()

    return {"message": "Image config deleted", "id": image_id}


# ==================== Sprint 18 Feature 24: Trace 回放 ====================

@app.get("/api/v1/tasks/{task_id}/traces")
async def get_task_traces(
    task_id: int,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """获取任务 Trace 列表（用于回放播放器）"""
    from app.models import Trace

    task = await session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await session.exec(
        select(Trace).where(Trace.task_id == task_id).order_by(Trace.id)
    )
    traces = result.all()

    return [
        {
            "id": trace.id,
            "agent_role": trace.agent_role,
            "perception_log": trace.perception_log,
            "reasoning_log": trace.reasoning_log,
            "applied_patch": trace.applied_patch,
            "is_success": trace.is_success,
            "timestamp": None,  # Trace 模型暂无 created_at 字段
        }
        for trace in traces
    ]


# ==================== Sprint 19: Tenant API Endpoints ====================

class TenantCreate(BaseModel):
    """租户创建模型"""
    name: str
    slug: str
    quota_tasks: Optional[int] = Field(default=100, ge=1)
    quota_storage_mb: Optional[int] = Field(default=1024, ge=64)
    quota_api_calls: Optional[int] = Field(default=10000, ge=100)


class TenantUpdate(BaseModel):
    """租户更新模型"""
    name: Optional[str] = None
    quota_tasks: Optional[int] = Field(None, ge=1)
    quota_storage_mb: Optional[int] = Field(None, ge=64)
    quota_api_calls: Optional[int] = Field(None, ge=100)
    is_active: Optional[bool] = None


@app.get("/api/v1/tenants")
async def list_tenants(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_read_key)
):
    """列出所有租户 - 需要 read 权限"""
    # 检查是否为 admin 权限
    if "admin" not in api_key.permissions:
        # 非 admin 只能看到自己租户
        tenant = await session.get(Tenant, api_key.tenant_id)
        if tenant:
            return [tenant.model_dump()]
        return []

    result = await session.exec(select(Tenant).order_by(Tenant.id))
    tenants = result.all()
    return [t.model_dump() for t in tenants]


@app.post("/api/v1/tenants")
async def create_tenant(
    tenant_in: TenantCreate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """创建租户 - 需要 admin 权限"""
    if "admin" not in api_key.permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")

    # 检查名称唯一性
    result = await session.exec(select(Tenant).where(Tenant.name == tenant_in.name))
    if result.one_or_none():
        raise HTTPException(status_code=409, detail="Tenant name already exists")

    # 检查 slug 唯一性
    result = await session.exec(select(Tenant).where(Tenant.slug == tenant_in.slug))
    if result.one_or_none():
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    # 创建租户
    new_tenant = Tenant(
        name=tenant_in.name,
        slug=tenant_in.slug,
        quota_tasks=tenant_in.quota_tasks,
        quota_storage_mb=tenant_in.quota_storage_mb,
        quota_api_calls=tenant_in.quota_api_calls
    )
    session.add(new_tenant)
    await session.commit()
    await session.refresh(new_tenant)

    return new_tenant.model_dump()


@app.get("/api/v1/tenants/me")
async def get_current_tenant(
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_read_key)
):
    """获取当前 API Key 所属租户信息"""
    tenant = await session.get(Tenant, api_key.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant.model_dump()


@app.get("/api/v1/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: int,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_read_key)
):
    """获取租户详情"""
    # 非 admin 只能查看自己租户
    if "admin" not in api_key.permissions and api_key.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant")

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    return tenant.model_dump()


@app.get("/api/v1/tenants/{tenant_id}/quota")
async def get_tenant_quota(
    tenant_id: int,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_read_key)
):
    """获取租户配额使用情况"""
    # 非 admin 只能查看自己租户配额
    if "admin" not in api_key.permissions and api_key.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Cannot access other tenant quota")

    usage = await get_quota_usage(tenant_id, session)
    return usage


@app.put("/api/v1/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: int,
    tenant_in: TenantUpdate,
    session: AsyncSession = Depends(get_db_session),
    api_key: APIKey = Depends(require_write_key)
):
    """更新租户 - 需要 admin 权限"""
    if "admin" not in api_key.permissions:
        raise HTTPException(status_code=403, detail="Admin permission required")

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    update_data = tenant_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)

    tenant.updated_at = datetime.now(timezone.utc)
    session.add(tenant)
    await session.commit()
    await session.refresh(tenant)

    return tenant.model_dump()
