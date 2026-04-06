import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

# Create an SQLite database in memory for testing, or a local file for deployment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///seca.db")

engine = create_async_engine(
    DATABASE_URL, 
    echo=False, 
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

def get_db_session() -> AsyncSession:
    """Dependency to provide database session."""
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()

# Trigger models to be imported so SQLModel.metadata registers them
import app.models
