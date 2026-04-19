"""Sprint 19: Tenant 隔离中间件与辅助函数 - Feature 22 Core"""
from fastapi import Request, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models import Tenant, APIKey
from app.database import engine
import hashlib
import secrets


def generate_api_key() -> str:
    """生成随机 API Key"""
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    """使用 SHA-256 哈希 API Key"""
    return hashlib.sha256(key.encode()).hexdigest()


async def get_tenant_from_api_key(api_key: str, session: AsyncSession) -> int:
    """
    从 API Key 解析 tenant_id

    Args:
        api_key: 原始 API Key 字符串
        session: 数据库 session

    Returns:
        tenant_id: 租户 ID

    Raises:
        HTTPException: API Key 无效或无租户绑定
    """
    # 获取所有活跃的 Key 进行验证
    result = await session.exec(
        select(APIKey).where(APIKey.is_active == True)
    )
    all_keys = result.all()

    # 遍历验证
    for key in all_keys:
        if hashlib.sha256(api_key.encode()).hexdigest() == key.key_hash:
            if key.tenant_id is None:
                raise HTTPException(status_code=401, detail="API Key has no tenant binding")
            return key.tenant_id

    raise HTTPException(status_code=401, detail="Invalid API Key")


async def init_default_tenant(session: AsyncSession) -> tuple[Tenant, str | None]:
    """
    初始化默认租户和默认 API Key（在系统启动时调用）

    Args:
        session: 数据库 session

    Returns:
        tuple: (默认租户对象, 默认 API Key 明文 或 None 如果已存在)
    """
    result = await session.exec(
        select(Tenant).where(Tenant.slug == "default")
    )
    existing = result.one_or_none()

    if existing:
        # 检查是否已有默认 API Key
        key_result = await session.exec(
            select(APIKey).where(
                APIKey.tenant_id == existing.id,
                APIKey.name == "default-key"
            )
        )
        existing_key = key_result.one_or_none()
        return (existing, None if existing_key else None)

    # 创建默认租户
    default_tenant = Tenant(
        name="Default Tenant",
        slug="default",
        quota_tasks=100,
        quota_storage_mb=1024,
        quota_api_calls=10000
    )
    session.add(default_tenant)
    await session.commit()
    await session.refresh(default_tenant)

    # 创建默认 API Key
    raw_key = generate_api_key()
    default_key = APIKey(
        name="default-key",
        key_hash=hash_api_key(raw_key),
        tenant_id=default_tenant.id,
        permissions=["read", "write"],
        is_active=True
    )
    session.add(default_key)
    await session.commit()

    return (default_tenant, raw_key)


async def get_quota_usage(tenant_id: int, session: AsyncSession) -> dict:
    """
    获取租户配额使用情况

    Args:
        tenant_id: 租户 ID
        session: 数据库 session

    Returns:
        dict: 配额使用信息
    """
    from app.models import Task, AuditLog

    # 获取租户信息
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # 计算任务使用量
    task_result = await session.exec(
        select(Task).where(Task.tenant_id == tenant_id)
    )
    tasks = task_result.all()
    tasks_used = len(tasks)

    # 计算存储使用量（简化实现：按任务数估算）
    storage_used_mb = tasks_used * 10  # 每个任务约 10MB

    # 计算 API 调用次数
    audit_result = await session.exec(
        select(AuditLog).where(AuditLog.tenant_id == tenant_id)
    )
    audits = audit_result.all()
    api_calls_used = len(audits)

    return {
        "tenant_id": tenant_id,
        "tasks_used": tasks_used,
        "tasks_quota": tenant.quota_tasks,
        "storage_used_mb": storage_used_mb,
        "storage_quota_mb": tenant.quota_storage_mb,
        "api_calls_used": api_calls_used,
        "api_calls_quota": tenant.quota_api_calls
    }


async def check_quota_limit(tenant_id: int, resource_type: str, session: AsyncSession) -> bool:
    """
    检查租户配额是否超限

    Args:
        tenant_id: 租户 ID
        resource_type: 资源类型 ("tasks", "storage", "api_calls")
        session: 数据库 session

    Returns:
        bool: 是否超限 (True = 超限, False = 未超限)
    """
    usage = await get_quota_usage(tenant_id, session)

    if resource_type == "tasks":
        return usage["tasks_used"] >= usage["tasks_quota"]
    elif resource_type == "storage":
        return usage["storage_used_mb"] >= usage["storage_quota_mb"]
    elif resource_type == "api_calls":
        return usage["api_calls_used"] >= usage["api_calls_quota"]

    return False