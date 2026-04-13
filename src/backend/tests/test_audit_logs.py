import pytest
from httpx import AsyncClient
from app.models import AuditLog
from app.main import app
from datetime import datetime, timezone, timedelta
from sqlmodel import SQLModel, select


@pytest.mark.asyncio
class TestAuditLogFields:
    """Sprint 11: 审计日志字段测试套件"""

    async def test_audit_log_captures_ip_address(self):
        """Red 路径：审计日志捕获 IP 地址"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "IPTestKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]
            key_id = create_key_res.json()["id"]

            # 执行写操作
            await client.post("/api/v1/projects", json={
                "name": "IPTestProject",
                "target_repo_path": "./ip-test"
            }, headers={"X-API-Key": api_key})

            # 验证审计日志包含 IP 地址
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

            # 查找最新的审计日志
            latest_log = logs[0]
            assert "ip_address" in latest_log, "审计日志应有 ip_address 字段"
            assert latest_log["ip_address"] is not None, "IP 地址不应为 None"
            # httpx test client 使用 127.0.0.1
            assert latest_log["ip_address"] in ["testclient", "127.0.0.1"], "IP 地址应为 testclient 或 127.0.0.1"

    async def test_audit_log_captures_user_agent(self):
        """Red 路径：审计日志捕获 User-Agent"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "UATestKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行写操作带自定义 User-Agent
            await client.post("/api/v1/projects", json={
                "name": "UATestProject",
                "target_repo_path": "./ua-test"
            }, headers={
                "X-API-Key": api_key,
                "User-Agent": "SECA-Test-Client/1.0"
            })

            # 验证审计日志包含 User-Agent
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

            # 查找包含 User-Agent 的审计日志
            ua_logs = [log for log in logs if log.get("user_agent")]
            assert len(ua_logs) > 0, "应有包含 User-Agent 的审计日志"

            # 验证 User-Agent 正确捕获
            latest_ua_log = ua_logs[0]
            assert latest_ua_log["user_agent"] == "SECA-Test-Client/1.0", "User-Agent 应正确捕获"

    async def test_audit_log_captures_api_key_id(self):
        """Red 路径：审计日志捕获 API Key ID"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "KeyIDTestKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]
            key_id = create_key_res.json()["id"]

            # 执行写操作
            await client.post("/api/v1/projects", json={
                "name": "KeyIDTestProject",
                "target_repo_path": "./keyid-test"
            }, headers={"X-API-Key": api_key})

            # 验证审计日志包含 API Key ID
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

            # 查找最新的审计日志
            latest_log = logs[0]
            assert "api_key_id" in latest_log, "审计日志应有 api_key_id 字段"
            assert latest_log["api_key_id"] == key_id, f"api_key_id 应为 {key_id}"

    async def test_audit_log_captures_duration(self):
        """Red 路径：审计日志捕获操作耗时"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "DurationTestKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行写操作
            await client.post("/api/v1/projects", json={
                "name": "DurationTestProject",
                "target_repo_path": "./duration-test"
            }, headers={"X-API-Key": api_key})

            # 验证审计日志包含 duration_ms
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

            # 查找最新的审计日志
            latest_log = logs[0]
            assert "duration_ms" in latest_log, "审计日志应有 duration_ms 字段"
            assert latest_log["duration_ms"] is not None, "duration_ms 不应为 None"
            assert isinstance(latest_log["duration_ms"], int), "duration_ms 应为整数"
            assert latest_log["duration_ms"] >= 0, "duration_ms 应 >= 0"


@pytest.mark.asyncio
class TestAuditLogFiltering:
    """Sprint 11: 审计日志查询过滤测试套件"""

    async def test_audit_logs_supports_time_range_filter(self):
        """Red 路径：审计日志支持时间范围筛选"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "TimeFilterKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行第一次写操作
            await client.post("/api/v1/projects", json={
                "name": "TimeFilterProject1",
                "target_repo_path": "./time-filter-1"
            }, headers={"X-API-Key": api_key})

            # 等待一小段时间
            import asyncio
            await asyncio.sleep(0.2)

            # 记录中间时间点
            middle_time = datetime.now(timezone.utc)

            await asyncio.sleep(0.2)

            # 执行第二次写操作
            await client.post("/api/v1/projects", json={
                "name": "TimeFilterProject2",
                "target_repo_path": "./time-filter-2"
            }, headers={"X-API-Key": api_key})

            # 等待审计日志写入
            await asyncio.sleep(0.1)

            # 使用 start_time 筛选（只获取之后的日志）
            start_time_str = middle_time.isoformat().replace("+00:00", "Z")
            filtered_res = await client.get(f"/api/v1/audit-logs?start_time={start_time_str}")
            filtered_logs = filtered_res.json()

            # 获取所有日志
            all_logs_res = await client.get("/api/v1/audit-logs")
            all_logs = all_logs_res.json()

            # 验证筛选有效：筛选后的日志应少于全部日志（因为只有第二次操作在 start_time 之后）
            assert len(filtered_logs) < len(all_logs), "时间筛选应返回更少的日志"

    async def test_audit_logs_supports_action_filter(self):
        """Red 路径：审计日志支持操作类型筛选"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "ActionFilterKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行 POST 操作
            create_res = await client.post("/api/v1/projects", json={
                "name": "ActionFilterProject",
                "target_repo_path": "./action-filter"
            }, headers={"X-API-Key": api_key})

            project_id = create_res.json()["id"]

            # 验证筛选 POST 操作
            post_filter_res = await client.get("/api/v1/audit-logs?action=POST")
            post_logs = post_filter_res.json()
            assert len(post_logs) > 0, "应有 POST 类型日志"
            for log in post_logs:
                assert log["action"] == "POST", "所有日志应为 POST 类型"

    async def test_audit_logs_supports_pagination(self):
        """Red 路径：审计日志支持分页"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "PaginationKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 创建多个项目以生成足够的日志
            for i in range(5):
                await client.post("/api/v1/projects", json={
                    "name": f"PaginationProject{i}",
                    "target_repo_path": f"./pagination-{i}"
                }, headers={"X-API-Key": api_key})

            # 测试分页：page=1, page_size=2
            page1_res = await client.get("/api/v1/audit-logs?page=1&page_size=2")
            page1_logs = page1_res.json()

            # 测试分页：page=2, page_size=2
            page2_res = await client.get("/api/v1/audit-logs?page=2&page_size=2")
            page2_logs = page2_res.json()

            # 验证分页有效
            assert len(page1_logs) == 2, "第一页应有 2 条日志"
            assert len(page2_logs) == 2, "第二页应有 2 条日志"
            assert page1_logs != page2_logs, "不同页的日志应不同"

    async def test_audit_logs_default_order_by_time(self):
        """Green 路径：审计日志默认按时间倒序"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "OrderKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 顺序创建三个项目
            project_names = ["OrderProject1", "OrderProject2", "OrderProject3"]
            for name in project_names:
                await client.post("/api/v1/projects", json={
                    "name": name,
                    "target_repo_path": f"./order-{name.lower()}"
                }, headers={"X-API-Key": api_key})

            # 获取审计日志（默认应倒序）
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()

            # 验证最新创建的在最后（因为倒序，所以应在列表前面）
            # 注意：由于可能有之前的日志，我们只验证最新三条的顺序
            recent_logs = [log for log in logs if log.get("details", {}).get("resource_name", "").startswith("OrderProject")]

            if len(recent_logs) >= 3:
                # 验证倒序：最新创建的应在最前面
                assert recent_logs[0]["details"]["resource_name"] == "OrderProject3", "最新日志应在最前"
                assert recent_logs[1]["details"]["resource_name"] == "OrderProject2", "次新日志应在第二"
                assert recent_logs[2]["details"]["resource_name"] == "OrderProject1", "最旧日志应在第三"


@pytest.mark.asyncio
class TestAuditLogIntegration:
    """Sprint 11: 审计日志集成测试套件"""

    async def test_write_operation_creates_audit_log(self):
        """Green 路径：写操作创建审计日志"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "WriteAuditKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行写操作
            res = await client.post("/api/v1/projects", json={
                "name": "WriteAuditProject",
                "target_repo_path": "./write-audit"
            }, headers={"X-API-Key": api_key})

            assert res.status_code == 200, "写操作应成功"
            project_id = res.json()["id"]

            # 验证审计日志被创建
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

            # 验证日志内容
            latest_log = logs[0]
            assert latest_log["action"] == "POST", "操作类型应为 POST"
            assert latest_log["api_key_id"] is not None, "应包含 API Key ID"
            assert latest_log["user_agent"] is not None, "应包含 User-Agent"
            assert latest_log["duration_ms"] is not None, "应包含 duration_ms"

    async def test_audit_log_full_payload(self):
        """Green 路径：审计日志完整字段验证"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "FullPayloadKey",
                "permissions": ["admin"]
            })
            api_key = create_key_res.json()["key"]
            key_id = create_key_res.json()["id"]

            # 执行写操作带完整 headers
            res = await client.post("/api/v1/projects", json={
                "name": "FullPayloadProject",
                "target_repo_path": "./full-payload"
            }, headers={
                "X-API-Key": api_key,
                "User-Agent": "SECA-Full-Test/1.0"
            })

            project_id = res.json()["id"]

            # 验证审计日志包含所有字段
            audit_res = await client.get("/api/v1/audit-logs")
            logs = audit_res.json()
            assert len(logs) > 0, "应有审计日志"

            latest_log = logs[0]

            # 验证所有必填字段
            required_fields = ["id", "action", "resource", "timestamp", "api_key_id", "user_agent", "duration_ms"]
            for field in required_fields:
                assert field in latest_log, f"审计日志应包含 {field}"

            # 验证字段值
            assert latest_log["action"] == "POST", "操作类型应为 POST"
            assert latest_log["api_key_id"] == key_id, f"api_key_id 应为 {key_id}"
            assert latest_log["user_agent"] == "SECA-Full-Test/1.0", "User-Agent 应正确捕获"
            assert latest_log["duration_ms"] >= 0, "duration_ms 应 >= 0"
            assert "projects" in latest_log["resource"]


@pytest.mark.asyncio
class TestAuditLogRegression:
    """Sprint 8/9/10: 审计日志回归测试套件"""

    async def test_audit_log_exists_on_write(self):
        """回归测试：Sprint 8 - 写操作有审计日志"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 创建 API Key
            create_key_res = await client.post("/api/v1/auth/api-keys", json={
                "name": "RegressionKey",
                "permissions": ["read", "write"]
            })
            api_key = create_key_res.json()["key"]

            # 执行写操作
            await client.post("/api/v1/projects", json={
                "name": "RegressionProject",
                "target_repo_path": "./regression"
            }, headers={"X-API-Key": api_key})

            # 验证审计日志存在
            audit_res = await client.get("/api/v1/audit-logs")
            assert audit_res.status_code == 200
            logs = audit_res.json()
            assert len(logs) > 0, "写操作应有审计日志"

    async def test_audit_logs_endpoint_returns_list(self):
        """回归测试：Sprint 8 - 审计端点返回列表"""
        from app.database import engine
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        from httpx import ASGITransport
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # 获取审计日志
            audit_res = await client.get("/api/v1/audit-logs")
            assert audit_res.status_code == 200
            logs = audit_res.json()
            assert isinstance(logs, list), "审计端点应返回列表"
