"""
Sprint 17: Docker 运维增强
测试 Docker 配置管理、容器监控、日志聚合功能
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestDockerConfig:
    """Docker 配置管理测试"""

    async def _get_api_key_header(self, client):
        """获取带写权限的 API Key 请求头"""
        key_res = await client.post("/api/v1/auth/api-keys", json={
            "name": "DockerTestKey",
            "permissions": ["read", "write", "admin"]
        })
        return {"X-API-Key": key_res.json()["key"]}

    async def test_docker_config_get(self):
        """获取 Docker 配置成功"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 首次获取配置（应返回默认值）
            response = await client.get("/api/v1/docker-config", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "memory_limit_mb" in data
            assert "cpu_limit" in data
            assert "timeout_seconds" in data
            assert "max_concurrent_containers" in data

    async def test_docker_config_update(self):
        """更新 Docker 配置成功"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 更新配置
            new_config = {
                "memory_limit_mb": 1024,
                "cpu_limit": 2,
                "timeout_seconds": 120,
                "max_concurrent_containers": 5
            }
            response = await client.put("/api/v1/docker-config", json=new_config, headers=headers)
            assert response.status_code == 200

            # 验证配置已更新
            get_response = await client.get("/api/v1/docker-config", headers=headers)
            assert get_response.status_code == 200
            data = get_response.json()
            assert data["memory_limit_mb"] == 1024
            assert data["cpu_limit"] == 2
            assert data["timeout_seconds"] == 120
            assert data["max_concurrent_containers"] == 5

    async def test_docker_config_validation_rejects_low_memory(self):
        """拒绝内存 < 64MB - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 32,  # 低于最小值
                "cpu_limit": 1,
                "timeout_seconds": 60,
                "max_concurrent_containers": 3
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            # FastAPI Pydantic 验证失败返回 422 Unprocessable Entity
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_high_memory(self):
        """拒绝内存 > 4GB - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 8192,  # 高于最大值
                "cpu_limit": 1,
                "timeout_seconds": 60,
                "max_concurrent_containers": 3
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            # FastAPI Pydantic 验证失败返回 422 Unprocessable Entity
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_low_cpu(self):
        """拒绝 CPU < 0.5 核 - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 512,
                "cpu_limit": 0.1,  # 低于最小值
                "timeout_seconds": 60,
                "max_concurrent_containers": 3
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_high_cpu(self):
        """拒绝 CPU > 4.0 核 - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 512,
                "cpu_limit": 8.0,  # 高于最大值
                "timeout_seconds": 60,
                "max_concurrent_containers": 3
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_low_timeout(self):
        """拒绝 timeout < 10 秒 - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 512,
                "cpu_limit": 1,
                "timeout_seconds": 5,  # 低于最小值
                "max_concurrent_containers": 3
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_high_timeout(self):
        """拒绝 timeout > 300 秒 - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 512,
                "cpu_limit": 1,
                "timeout_seconds": 600,  # 高于最大值
                "max_concurrent_containers": 3
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_low_containers(self):
        """拒绝 max_concurrent_containers < 1 - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 512,
                "cpu_limit": 1,
                "timeout_seconds": 60,
                "max_concurrent_containers": 0  # 低于最小值
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            assert response.status_code == 422

    async def test_docker_config_validation_rejects_high_containers(self):
        """拒绝 max_concurrent_containers > 10 - FastAPI Pydantic 返回 422"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            invalid_config = {
                "memory_limit_mb": 512,
                "cpu_limit": 1,
                "timeout_seconds": 60,
                "max_concurrent_containers": 20  # 高于最大值
            }
            response = await client.put("/api/v1/docker-config", json=invalid_config, headers=headers)
            assert response.status_code == 422


@pytest.mark.asyncio
class TestContainerMonitor:
    """容器监控测试"""

    async def _get_api_key_header(self, client):
        """获取带写权限的 API Key 请求头"""
        key_res = await client.post("/api/v1/auth/api-keys", json={
            "name": "ContainerTestKey",
            "permissions": ["read", "write"]
        })
        return {"X-API-Key": key_res.json()["key"]}

    async def test_container_monitor_get_stats(self):
        """获取容器统计成功"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 获取运行中容器列表
            response = await client.get("/api/v1/containers", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    async def test_container_history(self):
        """获取历史容器统计"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            response = await client.get("/api/v1/containers/history", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestDockerLogger:
    """Docker 日志服务测试"""

    async def _get_api_key_header(self, client):
        """获取带写权限的 API Key 请求头"""
        key_res = await client.post("/api/v1/auth/api-keys", json={
            "name": "LoggerTestKey",
            "permissions": ["read", "write"]
        })
        return {"X-API-Key": key_res.json()["key"]}

    async def test_docker_logger_get_logs(self):
        """获取容器日志成功"""
        from app.database import engine
        from sqlmodel import SQLModel
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = await self._get_api_key_header(client)

            # 先创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "LogTestProj",
                "target_repo_path": "./log-test"
            }, headers=headers)
            project_id = proj_res.json()["id"]

            # 创建任务
            task_res = await client.post("/api/v1/tasks", json={
                "project_id": project_id,
                "raw_objective": "Test logging"
            }, headers=headers)
            task_id = task_res.json()["id"]

            # 获取任务日志
            log_response = await client.get(f"/api/v1/tasks/{task_id}/logs", headers=headers)
            assert log_response.status_code == 200
            data = log_response.json()
            assert "logs" in data
            assert "total_lines" in data
            assert "truncated" in data
