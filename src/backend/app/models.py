from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict
import sqlalchemy as sa
from sqlalchemy import JSON

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    target_repo_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectConfig(SQLModel, table=True):
    """Sprint 6: 项目配置模型"""
    __tablename__ = "project_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id", unique=True)
    sandbox_timeout_seconds: int = Field(default=30, ge=1, le=60)
    max_memory_mb: int = Field(default=512, ge=128, le=2048)
    environment_variables: Dict[str, str] = Field(
        default_factory=dict,
        sa_type=sa.JSON
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Task(SQLModel, table=True):
    """Sprint 2 + Sprint 7: 任务模型（含队列支持）"""
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    raw_objective: str
    status: str = Field(default="PENDING")  # PENDING, QUEUED, RUNNING, COMPLETED, FAILED, CANCELLED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Sprint 7: 队列相关字段
    queue_position: Optional[int] = None  # 队列位置
    worker_id: Optional[str] = None  # 执行 Worker ID
    progress_percent: int = Field(default=0, ge=0, le=100)  # 进度百分比
    status_message: Optional[str] = None  # 进度状态消息

class Trace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    parent_trace_id: Optional[int] = Field(default=None, foreign_key="trace.id")
    agent_role: str
    perception_log: Optional[str] = None
    reasoning_log: Optional[str] = None
    applied_patch: Optional[str] = None
    is_success: bool = False

class Adr(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    brief_title: str
    generated_markdown_payload: str
