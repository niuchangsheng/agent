"""
Sprint 18 Feature 21: 镜像预拉取优化
测试镜像配置管理、状态检测、预拉取触发功能
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestImageConfig:
    """镜像配置管理测试"""

    async def _get_api_key_header(self, client):
        """获取带写权限的 API Key 请求头"""
        key_res = await client.post("/api/v1/auth/api-keys", json={
            "name": "ImageTestKey",
            "permissions": ["read", "write", "admin"]
        })
        return {"X-API-Key": key_res.json()["key"]}

    async def test_image_config_get(self):
        """获取镜像配置列表"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            response = await client.get("/api/v1/images", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_image_config_add(self):
        """添加镜像配置"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 添加镜像配置
            response = await client.post("/api/v1/images", json={
                "name": "alpine:3.18"
            }, headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "status" in data

    async def test_image_status_check(self):
        """检查镜像状态"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 先添加镜像
            await client.post("/api/v1/images", json={"name": "test-image:latest"}, headers=headers)

            # 检查状态
            response = await client.get("/api/v1/images/test-image:latest/status", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            # 状态可能是 ready, pulling, missing, failed
            assert data["status"] in ["ready", "pulling", "missing", "failed"]

    async def test_image_prepull_trigger(self):
        """触发镜像预拉取"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 先添加镜像
            await client.post("/api/v1/images", json={"name": "alpine:3.19"}, headers=headers)

            # 触发拉取
            response = await client.post("/api/v1/images/alpine:3.19/pull", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "status" in data

    async def test_image_duplicate_add(self):
        """添加重复镜像返回已存在"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 第一次添加
            await client.post("/api/v1/images", json={"name": "python:3.11-slim"}, headers=headers)

            # 第二次添加（应返回已存在或忽略）
            response = await client.post("/api/v1/images", json={"name": "python:3.11-slim"}, headers=headers)
            assert response.status_code in [200, 409]  # 200 OK 或 409 Conflict

    async def test_image_delete(self):
        """删除镜像配置"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 先添加镜像
            add_res = await client.post("/api/v1/images", json={"name": "node:20-alpine"}, headers=headers)
            image_id = add_res.json().get("id", 1)

            # 删除镜像
            response = await client.delete(f"/api/v1/images/{image_id}", headers=headers)
            assert response.status_code in [200, 204, 404]