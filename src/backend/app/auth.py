"""Sprint 8 + Sprint 10: API Key 认证与权限模块（bcrypt 加密）"""
from fastapi import Request, HTTPException, Depends
from sqlmodel import select
import bcrypt
import secrets
from datetime import datetime, timezone
from app.models import APIKey
from sqlmodel.ext.asyncio.session import AsyncSession


# bcrypt rounds 配置（平衡安全性和性能）
BCRYPT_ROUNDS = 12


def hash_api_key(key: str) -> str:
    """
    Sprint 10: 使用 bcrypt 哈希 API Key
    每次调用产生不同哈希（因为随机盐）
    """
    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    return bcrypt.hashpw(key.encode(), salt).decode()


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Sprint 10: 验证 API Key
    使用 bcrypt 验证，不暴露原始密钥
    """
    try:
        return bcrypt.checkpw(key.encode(), key_hash.encode())
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
