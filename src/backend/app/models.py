from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional, Dict
import sqlalchemy as sa
from sqlalchemy import JSON


class Tenant(SQLModel, table=True):
    """Sprint 19: 租户模型 - Feature 22 Core"""
    __tablename__ = "tenant"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)  # 租户名称，唯一
    slug: str = Field(unique=True)  # 租户标识符，唯一 (lowercase + hyphens)
    quota_tasks: int = Field(default=100, ge=1)  # 任务配额
    quota_storage_mb: int = Field(default=1024, ge=64)  # 存储配额 MB
    quota_api_calls: int = Field(default=10000, ge=100)  # API 调用配额
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    target_repo_path: str
    tenant_id: int = Field(default=1, foreign_key="tenant.id")  # Sprint 19: 租户隔离
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
    """Sprint 2 + Sprint 7 + Sprint 9 + Sprint 12 + Sprint 19: 任务模型（含队列支持、优先级、ETA、租户隔离）"""
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
    # Sprint 9: 优先级字段
    priority: int = Field(default=0, ge=0, le=10)  # 优先级 0-10
    # Sprint 12: ETA 字段
    estimated_remaining_seconds: Optional[int] = None  # 预计剩余时间（秒）
    estimated_completion_at: Optional[datetime] = None  # 预计完成时间
    # Sprint 19: 租户隔离
    tenant_id: int = Field(default=1, foreign_key="tenant.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Trace(SQLModel, table=True):
    """Sprint 2 + Sprint 19: Trace 模型（含租户隔离）"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    parent_trace_id: Optional[int] = Field(default=None, foreign_key="trace.id")
    agent_role: str
    perception_log: Optional[str] = None
    reasoning_log: Optional[str] = None
    applied_patch: Optional[str] = None
    is_success: bool = False
    # Sprint 19: 租户隔离
    tenant_id: int = Field(default=1, foreign_key="tenant.id")


class Adr(SQLModel, table=True):
    """Sprint 5 + Sprint 19: ADR 模型（含租户隔离）"""
    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: int = Field(foreign_key="task.id")
    brief_title: str
    generated_markdown_payload: str
    # Sprint 19: 租户隔离
    tenant_id: int = Field(default=1, foreign_key="tenant.id")


class APIKey(SQLModel, table=True):
    """Sprint 8 + Sprint 19: API Key 模型（含租户绑定）"""
    __tablename__ = "api_key"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    key_hash: str  # 哈希后的密钥
    permissions: list = Field(default_factory=list, sa_type=sa.JSON)  # read, write, admin
    # Sprint 19: 租户绑定
    tenant_id: int = Field(default=1, foreign_key="tenant.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_active: bool = Field(default=True)


class AuditLog(SQLModel, table=True):
    """Sprint 8 + Sprint 11 + Sprint 19: 审计日志模型（含租户归属）"""
    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None)  # 用户/API Key ID
    api_key_id: Optional[int] = Field(default=None)  # API Key ID (Sprint 11)
    action: str  # CREATE, DELETE, UPDATE 等
    resource: str  # 资源路径
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None  # Sprint 11: User-Agent
    duration_ms: Optional[int] = None  # Sprint 11: 操作耗时（毫秒）
    details: Optional[Dict[str, str]] = Field(default_factory=dict, sa_type=sa.JSON)
    # Sprint 19: 租户归属
    tenant_id: Optional[int] = Field(default=None, foreign_key="tenant.id")


class DockerConfig(SQLModel, table=True):
    """Sprint 17: Docker 沙箱配置模型"""
    __tablename__ = "docker_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    memory_limit_mb: int = Field(default=512, ge=64, le=4096)  # 内存限制 64MB-4GB
    cpu_limit: float = Field(default=1.0, ge=0.5, le=4.0)  # CPU 限制 0.5-4 核
    timeout_seconds: int = Field(default=60, ge=10, le=300)  # 超时 10-300 秒
    max_concurrent_containers: int = Field(default=3, ge=1, le=10)  # 最大并发容器数
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ImageConfig(SQLModel, table=True):
    """Sprint 18 Feature 21: 镜像预拉取配置模型"""
    __tablename__ = "image_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # 镜像名称，如 "alpine:3.18"
    status: str = Field(default="missing")  # ready, pulling, missing, failed
    last_pull_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
