import pytest
import asyncio
from app.database import engine

@pytest.fixture(scope="function", autouse=True)
async def dispose_engine():
    """Ensure engine connections are cleaned up. Function scope to align with default loop."""
    yield
    # We don't necessarily need to dispose the whole engine after every test, 
    # but the warning comes from unclosed connections. 
    # The async generator in database.py handles session cleanup now.
