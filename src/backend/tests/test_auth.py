import pytest
from httpx import AsyncClient
from app.models import Project, Task
from app.main import app
import hashlib


@pytest.mark.asyncio
class TestAPIKeyAuth:
    """Sprint 8: API Key 认证测试套件"""

    async def test_no_api_key_returns_401(self):
        """Red 路径：无 Key 请求返回 401"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 尝试创建项目（写操作）不带 API Key
            res = await client.post("/api/v1/projects", json={
                "name": "NoKeyTest",
                "target_repo_path": "./nokey"
            })
            assert res.status_code == 401, "写操作应要求 API Key 认证"

    async def test_invalid_api_key_returns_401(self):
        """Red 路径：无效 Key 返回 401"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 使用无效 API Key
            res = await client.post("/api/v1/projects", json={
                "name": "InvalidKeyTest",
                "target_repo_path": "./invalidkey"
            }, headers={"X-API-Key": "invalid-key-12345"})
            assert res.status_code == 401, "无效 Key 应被拒绝"

    async def test_readonly_key_cannot_write(self):
        """Red 路径：只读 Key 不能写操作"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 首先创建一个只读 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "ReadOnlyKey",
                "permissions": ["read"]
            })
            assert create_key_res.status_code == 200
            api_key = create_key_res.json()["key"]

            # 尝试写操作
            res = await client.post("/api/v1/projects", json={
                "name": "ReadOnlyTest",
                "target_repo_path": "./readonly"
            }, headers={"X-API-Key": api_key})
            assert res.status_code == 403, "只读 Key 应被拒绝写操作"

    async def test_api_key_creation(self):
        """Green 路径：创建 API Key"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res = await client.post("/api/v1/auth/api-keys", json={
                "name": "TestKey",
                "permissions": ["read", "write"]
            })
            assert res.status_code == 200
            result = res.json()
            assert "key" in result, "应返回 API Key"
            assert result["permissions"] == ["read", "write"]

    async def test_api_key_list(self):
        """Green 路径：列出 API Keys"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 先创建一个 Key
            await client.post("/api/v1/auth/api-keys", json={
                "name": "ListTestKey",
                "permissions": ["read"]
            })

            # 列出 Keys
            res = await client.get("/api/v1/auth/api-keys")
            assert res.status_code == 200
            result = res.json()
            assert isinstance(result, list), "应返回 Key 列表"

    async def test_api_key_delete(self):
        """Green 路径：删除 API Key"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 先创建一个 Key
            create_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "DeleteTestKey",
                "permissions": ["read"]
            })
            key_id = create_res.json()["id"]

            # 删除 Key
            delete_res = await client.delete(f"/api/v1/auth/api-keys/{key_id}")
            assert delete_res.status_code == 200

            # 验证 Key 已被删除
            list_res = await client.get("/api/v1/auth/api-keys")
            keys = list_res.json()
            assert not any(k["id"] == key_id for k in keys), "Key 应已被删除"

    async def test_write_operation_with_valid_key(self):
        """Green 路径：有效 Key 可执行写操作"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建带写权限的 Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "WriteKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 使用有效 Key 执行写操作
            res = await client.post("/api/v1/projects", json={
                "name": "ValidKeyTest",
                "target_repo_path": "./validkey"
            }, headers={"X-API-Key": api_key})
            assert res.status_code == 200, "有效写 Key 应允许写操作"

    async def test_audit_log_created_on_write(self):
        """Green 路径：写操作创建审计日志"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建带写权限的 Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "AuditKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行写操作
            await client.post("/api/v1/projects", json={
                "name": "AuditTest",
                "target_repo_path": "./audit"
            }, headers={"X-API-Key": api_key})

            # 验证审计日志被创建
            audit_res = await client.get("/api/v1/audit-logs")
            assert audit_res.status_code == 200
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

    async def test_middleware_protects_all_write_routes(self):
        """集成测试：中间件保护所有写路由"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 测试所有写路由都应要求认证
            write_routes = [
                ("POST", "/api/v1/projects", {"name": "Test", "target_repo_path": "./test"}),
                ("POST", "/api/v1/tasks/queue", {"project_id": 1, "raw_objective": "Test"}),
            ]

            for method, path, data in write_routes:
                if method == "POST":
                    res = await client.post(path, json=data)
                assert res.status_code == 401, f"{method} {path} 应要求认证"

    async def test_read_operation_without_key(self):
        """Green 路径：读操作无需 Key (可选功能)"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 健康检查应无需认证
            res = await client.get("/api/v1/health")
            assert res.status_code == 200
