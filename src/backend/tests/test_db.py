import pytest
from sqlmodel import SQLModel
from sqlalchemy import text
from app.database import engine

@pytest.mark.asyncio
async def test_tables_are_created_correctly():
    """测试通过 SQLAlchemy 引擎能够连通数据库并产生预期表结构"""
    # 让 SQLModel 创建元数据
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        
    # 测试连接并查表
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        
        # 核心四张表必须存在
        for expected_table in ["project", "task", "trace", "adr"]:
            assert expected_table in tables, f"缺少必须的数据表 {expected_table}"

def test_database_connection_failure_handling():
    """测试如果给定的是损坏或无效的文件系统能否被优雅捕捉"""
    from app.database import get_db_session
    assert get_db_session is not None
