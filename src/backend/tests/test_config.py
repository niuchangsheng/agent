import pytest
from httpx import AsyncClient
from sqlmodel import select
from app.models import Project, ProjectConfig
from app.main import app


@pytest.mark.asyncio
class TestProjectConfig:
    """Sprint 6: 配置管理中心测试套件"""

    async def test_config_create_and_get(self):
        """Green 路径：创建并获取配置"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "TestProj",
                "target_repo_path": "./test"
            })
            proj_id = proj_res.json()["id"]

            # 创建配置
            config_data = {
                "sandbox_timeout_seconds": 45,
                "max_memory_mb": 1024,
                "environment_variables": {"API_KEY": "test123", "DEBUG": "true"}
            }
            config_res = await client.post(f"/api/v1/projects/{proj_id}/config", json=config_data)
            assert config_res.status_code == 200
            result = config_res.json()
            assert result["sandbox_timeout_seconds"] == 45
            assert result["max_memory_mb"] == 1024

            # 获取配置
            get_res = await client.get(f"/api/v1/projects/{proj_id}/config")
            assert get_res.status_code == 200
            get_result = get_res.json()
            assert get_result["sandbox_timeout_seconds"] == 45
            assert get_result["environment_variables"]["API_KEY"] == "test123"

    async def test_config_update(self):
        """Green 路径：更新配置"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "TestProj2",
                "target_repo_path": "./test2"
            })
            proj_id = proj_res.json()["id"]

            # 创建初始配置
            await client.post(f"/api/v1/projects/{proj_id}/config", json={
                "sandbox_timeout_seconds": 30,
                "max_memory_mb": 512,
                "environment_variables": {}
            })

            # 更新配置
            update_data = {
                "sandbox_timeout_seconds": 60,
                "max_memory_mb": 2048,
                "environment_variables": {"NEW_VAR": "value"}
            }
            update_res = await client.put(f"/api/v1/projects/{proj_id}/config", json=update_data)
            assert update_res.status_code == 200
            result = update_res.json()
            assert result["sandbox_timeout_seconds"] == 60
            assert result["max_memory_mb"] == 2048
            assert result["environment_variables"]["NEW_VAR"] == "value"

    async def test_config_not_found_returns_404(self):
        """Red 路径：项目不存在时返回 404"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 获取不存在的配置
            res = await client.get("/api/v1/projects/99999/config")
            assert res.status_code == 404

    async def test_config_create_invalid_project_id(self):
        """Red 路径：无效 project_id 创建失败"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建配置到不存在的项目
            config_res = await client.post("/api/v1/projects/99999/config", json={
                "sandbox_timeout_seconds": 30,
                "max_memory_mb": 512,
                "environment_variables": {}
            })
            assert config_res.status_code == 400

    async def test_config_timeout_out_of_range(self):
        """Red 路径：超时超出范围验证"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "TestProj3",
                "target_repo_path": "./test3"
            })
            proj_id = proj_res.json()["id"]

            # 超时设置为 0 (小于最小值 1)
            config_res = await client.post(f"/api/v1/projects/{proj_id}/config", json={
                "sandbox_timeout_seconds": 0,
                "max_memory_mb": 512,
                "environment_variables": {}
            })
            assert config_res.status_code == 422  # 验证错误

            # 超时设置为 1000 (大于最大值 60)
            config_res = await client.post(f"/api/v1/projects/{proj_id}/config", json={
                "sandbox_timeout_seconds": 1000,
                "max_memory_mb": 512,
                "environment_variables": {}
            })
            assert config_res.status_code == 422

    async def test_config_memory_out_of_range(self):
        """Red 路径：内存超出范围验证"""
        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建项目
            proj_res = await client.post("/api/v1/projects", json={
                "name": "TestProj4",
                "target_repo_path": "./test4"
            })
            proj_id = proj_res.json()["id"]

            # 内存设置为 50 (小于最小值 128)
            config_res = await client.post(f"/api/v1/projects/{proj_id}/config", json={
                "sandbox_timeout_seconds": 30,
                "max_memory_mb": 50,
                "environment_variables": {}
            })
            assert config_res.status_code == 422

            # 内存设置为 10000 (大于最大值 2048)
            config_res = await client.post(f"/api/v1/projects/{proj_id}/config", json={
                "sandbox_timeout_seconds": 30,
                "max_memory_mb": 10000,
                "environment_variables": {}
            })
            assert config_res.status_code == 422

    async def test_config_isolation(self):
        """Green 路径：3 个并发任务各自遵循独立配额"""
        from app.database import engine
        async with engine.begin() as conn:
            from sqlmodel import SQLModel
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 3 个项目，每个有不同的配置
            configs = [
                {"timeout": 20, "memory": 256},
                {"timeout": 40, "memory": 1024},
                {"timeout": 60, "memory": 2048}
            ]

            project_ids = []
            for i, cfg in enumerate(configs):
                proj_res = await client.post("/api/v1/projects", json={
                    "name": f"IsolationProj{i}",
                    "target_repo_path": f"./test{i}"
                })
                proj_id = proj_res.json()["id"]
                project_ids.append(proj_id)

                config_res = await client.post(f"/api/v1/projects/{proj_id}/config", json={
                    "sandbox_timeout_seconds": cfg["timeout"],
                    "max_memory_mb": cfg["memory"],
                    "environment_variables": {"PROJECT_ID": str(i)}
                })
                assert config_res.status_code == 200
                result = config_res.json()
                assert result["sandbox_timeout_seconds"] == cfg["timeout"]
                assert result["max_memory_mb"] == cfg["memory"]

            # 验证每个配置独立存储
            for i, cfg in enumerate(configs):
                proj_id = project_ids[i]
                get_res = await client.get(f"/api/v1/projects/{proj_id}/config")
                assert get_res.status_code == 200
                result = get_res.json()
                assert result["sandbox_timeout_seconds"] == cfg["timeout"]
                assert result["max_memory_mb"] == cfg["memory"]
                assert result["environment_variables"]["PROJECT_ID"] == str(i)
