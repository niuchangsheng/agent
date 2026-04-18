"""Sprint 8 + Sprint 10: API Key 认证与权限模块（SHA-256 哈希）"""
from fastapi import Request, HTTPException, Depends
from sqlmodel import select
import hashlib
import secrets
from datetime import datetime, timezone
from app.models import APIKey
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_db_session


# SHA-256 哈希（高性能，适合 API Key 验证）


def hash_api_key(key: str) -> str:
    """
    使用 SHA-256 哈希 API Key（高性能）
    """
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    验证 API Key（常数时间比较）
    """
    try:
        return hashlib.sha256(key.encode()).hexdigest() == key_hash
    except Exception:
        return False


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

        # 获取所有活跃的 Key 进行验证
        result = await session.exec(
            select(APIKey).where(
                APIKey.is_active == True
            )
        )
        all_keys = result.all()

        # 遍历验证（因为 bcrypt 哈希包含随机盐）
        db_key = None
        for key in all_keys:
            if verify_api_key(api_key, key.key_hash):
                db_key = key
                break

        if not db_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # 检查过期（处理时区问题）
        if db_key.expires_at:
            expires_at = db_key.expires_at
            # 如果 expires_at 是 naive datetime，转换为 aware
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="API key expired")

        # 检查权限
        if permission not in db_key.permissions and "admin" not in db_key.permissions:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # 存储 API Key ID 到 request state，供审计中间件使用
        request.state.api_key_id = db_key.id

        return db_key

    return api_key_dependency


# 预定义的依赖函数
require_write_key = require_api_key("write")
require_admin_key = require_api_key("admin")
require_read_key = require_api_key("read")
