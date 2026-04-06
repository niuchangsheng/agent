import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlmodel import SQLModel

from app.database import engine

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize the database tables on startup
    # Since we are using aiosqlite, we use run_sync for creating tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Cleanup resources
    await engine.dispose()

app = FastAPI(
    title="SECA - Diagnostic API",
    description="Backend Service for the Self-Evolving Coding Agent",
    lifespan=lifespan
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "active"}

@app.exception_handler(404)
async def custom_404_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
