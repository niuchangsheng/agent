# Sprint 19 验收合同：多租户架构 (上) — Feature 22 (核心)

## 合同签署方
- **需求方**: product_spec.md Feature 22 (Sprint 19)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能概述
本 Sprint 实现多租户架构的核心隔离能力：
1. **Tenant 数据模型**: 租户实体与配额定义
2. **Project/Task/... 模型扩展**: 所有核心模型新增 tenant_id
3. **租户隔离中间件**: 自动注入 tenant_id 到 request.state
4. **Tenant API 端点**: 租户管理与配额监控
5. **数据隔离测试**: 越权访问 100% 拒绝

---

## Part A: Tenant 数据模型

### 后端单元测试 (`src/backend/tests/test_tenant.py`) - 7 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_tenant_create` | POST /api/v1/tenants 创建租户成功 | [ ] |
| `test_tenant_name_unique` | 创建同名租户返回 409 Conflict | [ ] |
| `test_tenant_slug_unique` | 创建相同 slug 返回 409 Conflict | [ ] |
| `test_tenant_default_quota` | 新租户配额默认值正确 | [ ] |
| `test_tenant_list` | GET /api/v1/tenants 返回租户列表 | [ ] |
| `test_tenant_detail` | GET /api/v1/tenants/{id} 返回详情 | [ ] |
| `test_tenant_quota_usage` | GET /api/v1/tenants/{id}/quota 返回使用量 | [ ] |

### Tenant 数据模型

```python
class Tenant(SQLModel, table=True):
    __tablename__ = "tenant"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str  # 租户名称，唯一
    slug: str  # 租户标识符，唯一 (lowercase + hyphens)
    quota_tasks: int = Field(default=100, ge=1)  # 任务配额
    quota_storage_mb: int = Field(default=1024, ge=64)  # 存储配额
    quota_api_calls: int = Field(default=10000, ge=100)  # API 调用配额
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

## Part B: Project/Task 模型扩展

### 后端单元测试 (`src/backend/tests/test_tenant_isolation.py`) - 5 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_cross_tenant_project_access_denied` | Tenant A 无法访问 Tenant B 的项目 | [ ] |
| `test_cross_tenant_task_access_denied` | Tenant A 无法查询 Tenant B 的任务 | [ ] |
| `test_cross_tenant_trace_access_denied` | Tenant A 无法获取 Tenant B 的 Trace | [ ] |
| `test_tenant_scope_auto_filter` | list API 自动按 tenant_id 篇选 | [ ] |
| `test_apikey_tenant_binding` | API Key 必须绑定 tenant_id | [ ] |

### 模型扩展要求

| 模型 | 新增字段 | 约束 |
|------|----------|------|
| Project | `tenant_id: int` | 外键 tenant.id，必填 |
| Task | `tenant_id: int` | 外键 tenant.id，必填 |
| Trace | `tenant_id: int` | 外键 tenant.id，必填 |
| Adr | `tenant_id: int` | 外键 tenant.id，必填 |
| APIKey | `tenant_id: int` | 外键 tenant.id，必填 |
| AuditLog | `tenant_id: int` | 外键 tenant.id，可选 (记录操作者租户) |

---

## Part C: API Key 租户绑定测试

### 后端单元测试 (`src/backend/tests/test_apikey_tenant.py`) - 4 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_apikey_bind_tenant` | 新建 API Key 必须绑定 tenant_id | [ ] |
| `test_default_tenant_apikey` | 首次创建 API Key 自动绑定 tenant_id=1 | [ ] |
| `test_apikey_list_tenant_scope` | Tenant A 只能看到自己租户的 Key | [ ] |
| `test_cross_tenant_key_rejected` | Tenant A 的 Key 无法认证 Tenant B 的操作 | [ ] |

---

## Part D: Tenant API 端点

| 端点 | 方法 | 权限 | 功能 |
|------|------|------|------|
| `/api/v1/tenants` | GET | admin | 列出所有租户 |
| `/api/v1/tenants` | POST | admin | 创建新租户 |
| `/api/v1/tenants/{tenant_id}` | GET | admin | 获取租户详情 |
| `/api/v1/tenants/{tenant_id}/quota` | GET | admin | 获取配额使用情况 |
| `/api/v1/tenants/me` | GET | read | 获取当前租户信息 |

### API 响应格式

**Tenant Create Request**:
```json
{
  "name": "ACME Corporation",
  "slug": "acme-corp",
  "quota_tasks": 200,
  "quota_storage_mb": 2048
}
```

**Tenant Quota Response**:
```json
{
  "tenant_id": 1,
  "tasks_used": 45,
  "tasks_quota": 100,
  "storage_used_mb": 256,
  "storage_quota_mb": 1024,
  "api_calls_used": 1234,
  "api_calls_quota": 10000
}
```

---

## 完成定义

- [ ] Tenant 模型测试全部通过 (7 tests)
- [ ] Tenant 隔离测试全部通过 (5 tests)
- [ ] API Key 绑定测试全部通过 (4 tests)
- [ ] Tenant API 端点正常响应
- [ ] 默认租户 (tenant_id=1) 自动创建
- [ ] 所有现有端点添加 tenant_id 过滤
- [ ] 回归测试：Sprint 1-18 全量测试通过
- [ ] handoff.md 更新完成

---

## 技术备注

### Tenant 隔离中间件实现要点
```python
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    # 从 API Key 解析 tenant_id
    api_key = request.headers.get("X-API-Key")
    if api_key:
        tenant_id = await get_tenant_from_api_key(api_key)
        request.state.tenant_id = tenant_id
    return await call_next(request)
```

### 默认租户初始化
```python
async def init_default_tenant():
    # 在 lifespan 中检查并创建默认租户
    result = await session.exec(select(Tenant).where(Tenant.slug == "default"))
    if not result.one_or_none():
        default = Tenant(name="Default Tenant", slug="default")
        session.add(default)
        await session.commit()
```

### 配额检查位置
- 创建任务前检查 `quota_tasks`
- 超过配额返回 HTTPException(status_code=429)

---

## 安全边界声明

⚠️ **强制隔离原则**: 所有数据库查询必须附加 `WHERE tenant_id = ?` 过滤。
任何绕过 tenant_id 过滤的查询视为 **P0 安全漏洞**，QA 评审直接打回。

---

**签署时间**: 2026-04-19
**Generator 签名**: Sprint 19 开发启动