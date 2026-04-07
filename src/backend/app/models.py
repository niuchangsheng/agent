from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    target_repo_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    raw_objective: str
    status: str = Field(default="PENDING")
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
