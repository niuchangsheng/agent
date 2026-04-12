"""Sprint 8: API Key 认证与权限模块"""
from fastapi import Request, HTTPException, Depends
from sqlmodel import select
import hashlib
import secrets
from datetime import datetime, timezone
from app.models import APIKey
from sqlmodel.ext.asyncio.session import AsyncSession


def hash_api_key(key: str) -> str:
    """哈希 API Key"""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> str:
    """生成随机 API Key"""
    return secrets.token_urlsafe(32)


def require_api_key(permission: str = "write"):
    """返回一个依赖函数，用于验证 API Key"""

    async def api_key_dependency(
        request: Request,
        session: AsyncSession = Depends(get_db_session)
    ) -> APIKey:
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")

        key_hash = hash_api_key(api_key)
        result = await session.exec(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True
            )
        )
        db_key = result.one_or_none()

        if not db_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # 检查过期
        if db_key.expires_at and db_key.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="API key expired")

        # 检查权限
        if permission not in db_key.permissions and "admin" not in db_key.permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return db_key

    return api_key_dependency


async def get_db_session():
    """获取数据库会话"""
    from app.database import get_db_session
    async for session in get_db_session():
        yield session


# 预定义的依赖函数
require_write_key = require_api_key("write")
require_admin_key = require_api_key("admin")
require_read_key = require_api_key("read")
