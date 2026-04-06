import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlmodel import SQLModel

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

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
