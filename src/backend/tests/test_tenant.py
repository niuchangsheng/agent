"""Sprint 19: Tenant 模型测试 - Feature 22 Core"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import engine
from app.main import app
from app.models import Tenant, Project, Task, APIKey


@pytest.fixture
async def setup_tenant_db():
    """Tenant 测试数据库初始化"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # 清理旧数据
        result = await session.exec(select(Tenant))
        for t in result.all():
            await session.delete(t)
        result = await session.exec(select(APIKey))
        for k in result.all():
            await session.delete(k)
        result = await session.exec(select(Project))
        for p in result.all():
            await session.delete(p)
        await session.commit()

        # 创建默认租户
        default_tenant = Tenant(name="Default Tenant", slug="default")
        session.add(default_tenant)
        await session.commit()
        await session.refresh(default_tenant)

        # 立即捕获 ID
        default_tenant_id = default_tenant.id

        yield {"session": session, "default_tenant_id": default_tenant_id}


@pytest.fixture
async def admin_client(setup_tenant_db):
    """提供带 admin 权限的客户端"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 创建 admin API Key
        key_res = await client.post("/api/v1/auth/api-keys", json={
            "name": "AdminKey",
            "permissions": ["admin"],
            "tenant_id": setup_tenant_db["default_tenant_id"]
        })
        # 如果返回 400，说明 API 还不支持 tenant_id，使用无 tenant_id 版本
        if key_res.status_code == 400:
            key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "AdminKey",
                "permissions": ["admin"]
            })
        api_key = key_res.json().get("key", "")
        headers = {"X-API-Key": api_key}

        yield client, headers, setup_tenant_db


# TC-T001: 创建租户 (Happy Path)
@pytest.mark.asyncio
async def test_tenant_create(admin_client):
    """测试创建租户成功"""
    client, headers, setup_data = admin_client

    response = await client.post(
        "/api/v1/tenants",
        json={
            "name": "ACME Corporation",
            "slug": "acme-corp",
            "quota_tasks": 200
        },
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "ACME Corporation"
    assert data["slug"] == "acme-corp"
    assert data["quota_tasks"] == 200
    assert data["id"] is not None


# TC-T002: 租户名称唯一性约束
@pytest.mark.asyncio
async def test_tenant_name_unique(admin_client):
    """测试同名租户创建返回 409"""
    client, headers, setup_data = admin_client

    # 创建第一个租户
    await client.post(
        "/api/v1/tenants",
        json={"name": "Unique Name Test", "slug": "unique-name-1"},
        headers=headers
    )

    # 创建同名租户
    response = await client.post(
        "/api/v1/tenants",
        json={"name": "Unique Name Test", "slug": "unique-name-2"},
        headers=headers
    )

    assert response.status_code == 409


# TC-T003: 租户 slug 唯一性约束
@pytest.mark.asyncio
async def test_tenant_slug_unique(admin_client):
    """测试相同 slug 创建返回 409"""
    client, headers, setup_data = admin_client

    # 创建第一个租户
    await client.post(
        "/api/v1/tenants",
        json={"name": "Slug Test 1", "slug": "unique-slug-test"},
        headers=headers
    )

    # 创建相同 slug 租户
    response = await client.post(
        "/api/v1/tenants",
        json={"name": "Slug Test 2", "slug": "unique-slug-test"},
        headers=headers
    )

    assert response.status_code == 409


# TC-T004: 租户配额默认值
@pytest.mark.asyncio
async def test_tenant_default_quota(admin_client):
    """测试新租户配额默认值"""
    client, headers, setup_data = admin_client

    response = await client.post(
        "/api/v1/tenants",
        json={"name": "Default Quota Test", "slug": "default-quota"},
        headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["quota_tasks"] == 100  # 默认值
    assert data["quota_storage_mb"] == 1024  # 默认值
    assert data["quota_api_calls"] == 10000  # 默认值


# TC-T005: 租户列表 API
@pytest.mark.asyncio
async def test_tenant_list(admin_client):
    """测试获取租户列表"""
    client, headers, setup_data = admin_client

    # 创建几个租户
    await client.post(
        "/api/v1/tenants",
        json={"name": "List Test 1", "slug": "list-test-1"},
        headers=headers
    )
    await client.post(
        "/api/v1/tenants",
        json={"name": "List Test 2", "slug": "list-test-2"},
        headers=headers
    )

    response = await client.get("/api/v1/tenants", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3  # default + 2 created


# TC-T006: 租户详情 API
@pytest.mark.asyncio
async def test_tenant_detail(admin_client):
    """测试获取租户详情"""
    client, headers, setup_data = admin_client

    # 创建租户
    create_res = await client.post(
        "/api/v1/tenants",
        json={"name": "Detail Test", "slug": "detail-test"},
        headers=headers
    )
    tenant_id = create_res.json()["id"]

    response = await client.get(f"/api/v1/tenants/{tenant_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Detail Test"
    assert data["slug"] == "detail-test"


# TC-T007: 租户配额查询
@pytest.mark.asyncio
async def test_tenant_quota_usage(admin_client):
    """测试获取租户配额使用情况"""
    client, headers, setup_data = admin_client
    tenant_id = setup_data["default_tenant_id"]

    response = await client.get(f"/api/v1/tenants/{tenant_id}/quota", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "tasks_used" in data
    assert "tasks_quota" in data
    assert "storage_used_mb" in data
    assert "storage_quota_mb" in data


# TC-T008: 当前租户信息 (tenants/me)
@pytest.mark.asyncio
async def test_tenant_me(admin_client):
    """测试获取当前租户信息"""
    client, headers, setup_data = admin_client

    response = await client.get("/api/v1/tenants/me", headers=headers)

    # 打印响应详情以便调试
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "slug" in data