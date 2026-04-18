# QA 评审报告：Sprint 19 多租户架构 (上)

## 评审信息
- **评审日期**: 2026-04-19
- **评审方**: SECA Evaluator (零容忍 QA)
- **评审对象**: Sprint 19 Feature 22 (多租户架构核心)
- **评审类型**: 功能验收 + 安全审计

---

## 冒烟门禁测试 (BLOCKER)

### 后端服务
```bash
$ curl -s http://localhost:8000/api/v1/health
{"status":"active"}
```
**结果**: ✅ PASS

### 前端服务
```bash
$ curl -s http://localhost:5174/
<!doctype html>
<html lang="en">...
```
**结果**: ✅ PASS

---

## 🚨 P0 安全漏洞 (BLOCKER - 直接打回)

### 漏洞描述
多个 API 端点未添加 `tenant_id` 过滤，导致跨租户数据泄露。

### 证据
```bash
# Tenant B API Key 查看项目列表 (应只能看到 Tenant B 的项目)
$ curl -s http://localhost:8000/api/v1/projects -H "X-API-Key: ydKqaN82Tt29aZv1WZ5EYiiruUvggYaMckH5E9FC_lg"

# 实际返回: Tenant A 的项目也被返回！
[
  {"id":2,"tenant_id":1,"name":"SECA Agent",...},  # ← Tenant A 的项目
  {"id":1,"tenant_id":1,"name":"Tenant B Project",...}
]
```

### 违规端点清单

| 端点 | 文件行号 | 违规类型 |
|------|----------|----------|
| `/api/v1/projects` | Line 243 | `select(Project)` 无 tenant_id 过滤 |
| `/api/v1/tasks` | Line 262 | `select(Task)` 无 tenant_id 过滤 |
| `/api/v1/tasks/{id}/dag-tree` | Line 292 | 仅 task_id 过滤，无 tenant_id |
| `/api/v1/tasks/{id}/generate-adr` | Line 325-330 | 仅 task_id 过滤，无 tenant_id |
| `/api/v1/containers` | Line 959 | `select(Task)` 无 tenant_id 过滤 |
| `/api/v1/tasks/{id}/logs` | Line 1028-1076 | Trace 查询无 tenant_id 过滤 |

### 合同违规声明
> ⚠️ **强制隔离原则**: 所有数据库查询必须附加 `WHERE tenant_id = ?` 过滤。
> 任何绕过 tenant_id 过滤的查询视为 **P0 安全漏洞**，QA 评审直接打回。

---

## TDD 合规审计

### 测试执行
```bash
$ pytest tests/test_tenant.py tests/test_tenant_isolation.py tests/test_apikey_tenant.py -v
======================== 19 passed ========================
```

### 测试覆盖分析
| 测试文件 | 测试数 | 状态 | 覆盖范围 |
|----------|--------|------|----------|
| test_tenant.py | 8 | ✅ | Tenant CRUD, quota, uniqueness |
| test_tenant_isolation.py | 6 | ✅ | 跨租户访问拒绝 (数据库层) |
| test_apikey_tenant.py | 5 | ✅ | APIKey tenant_id 绑定 |

### TDD 评价
- ✅ 测试先行执行 (Red → Green → Refactor)
- ❌ **测试未覆盖 API 端点的 tenant_id 过滤**
  - `test_tenant_isolation.py` 仅测试数据库层隔离
  - 未测试 `/api/v1/projects`、`/api/v1/tasks` 等端点的实际响应隔离

---

## Tenant API 端点实测

### 成功端点
| 端点 | 状态 | 证据 |
|------|------|------|
| POST /api/v1/tenants | ✅ 200 | 创建租户成功，返回 id=2 |
| GET /api/v1/tenants | ✅ 200 | 返回租户列表 |
| GET /api/v1/tenants/{id} | ✅ 200 | 返回租户详情 |
| GET /api/v1/tenants/{id}/quota | ✅ 200 | 返回配额使用情况 |
| GET /api/v1/tenants/me | ✅ 200 | 返回当前租户信息 |

### 唯一性约束测试
```bash
# 创建同名租户
$ curl -s -w "%{http_code}" POST /api/v1/tenants -d '{"name": "Test Tenant", "slug": "different"}'
{"detail":"Tenant name already exists"} 409 ✅

# 创建相同 slug
$ curl -s -w "%{http_code}" POST /api/v1/tenants -d '{"name": "Different", "slug": "test-tenant"}'
{"detail":"Tenant slug already exists"} 409 ✅
```

---

## 回归测试

| Sprint | 端点 | 状态 |
|--------|------|------|
| Sprint 17 | /api/v1/docker-config | ✅ 200 |
| Sprint 18 | /api/v1/images | ✅ 200 |
| Sprint 13 | /api/v1/metrics | ✅ 200 |

---

## 四维评分

### 1. 功能完整性 (35%)

| 验收项 | 状态 | 证据 |
|--------|------|------|
| Tenant 数据模型 | ✅ | 8 tests 通过 |
| tenant_id 扩展 | ✅ | Project/Task/Trace/Adr/APIKey/AuditLog 新增字段 |
| Tenant API 端点 | ✅ | 5 端点正常响应 |
| 唯一性约束 | ✅ | 409 Conflict |
| 默认租户自动创建 | ✅ | tenant_id=1 自动绑定 |
| **API 端点 tenant_id 过滤** | ❌ **FAIL** | Tenant B 可见 Tenant A 数据 |

**得分**: **3/10** (P0 安全漏洞 = 功能完整性 ≤ 5)

### 2. 设计工程质量 (25%)

| 指标 | 评估 |
|------|------|
| Tenant 模型设计 | ✅ 字段完整 (quota_tasks/storage/api_calls) |
| API 响应格式 | ✅ 规范 JSON |
| TypeScript 类型 | ✅ N/A (本 Sprint 无前端) |

**得分**: **7/10**

### 3. 代码内聚素质 (20%)

| 指标 | 评估 |
|------|------|
| 后端测试覆盖 | ✅ 19 tests |
| TDD 流程 | ✅ Red→Green→Refactor |
| **端点隔离测试覆盖** | ❌ **FAIL** | 未测试 API 层 tenant_id 过滤 |

**得分**: **4/10** (安全测试缺失)

### 4. 用户体验 (20%)

| 指标 | 评估 |
|------|------|
| 本 Sprint 无前端交付 | N/A |
| 回归验证 | ✅ 前端未破坏 |

**得分**: **7/10** (基线保持分)

---

## 加权总分

| 维度 | 分数 | 权重 | 加权分 |
|------|------|------|--------|
| 功能完整性 | 3/10 | 35% | 1.05 |
| 设计工程质量 | 7/10 | 25% | 1.75 |
| 代码内聚素质 | 4/10 | 20% | 0.80 |
| 用户体验 | 7/10 | 20% | 1.40 |
| **总计** | - | 100% | **5.00** |

---

## 评审结论

**❌ FAIL** - 加权总分 5.00 < 7.0
**❌ FAIL** - 功能完整性 3 < 6
**❌ FAIL** - 代码内聚素质 4 < 6

### 主要原因
1. **P0 安全漏洞**: API 端点缺少 tenant_id 过滤，违反合同强制隔离原则
2. **测试覆盖不足**: 仅测试数据库层隔离，未测试 API 层实际隔离效果

---

## 🔧 整改指导

### 必修项 (MUST FIX)

1. **修改 `list_projects` 端点**
```python
# 当前代码 (Line 243)
result = await session.exec(select(Project).order_by(Project.id.desc()))

# 应改为
result = await session.exec(
    select(Project)
    .where(Project.tenant_id == api_key.tenant_id)
    .order_by(Project.id.desc())
)
```

2. **修改 `list_tasks` 端点** (Line 262)
```python
# 应添加 tenant_id 过滤
result = await session.exec(
    select(Task)
    .where(Task.tenant_id == api_key.tenant_id)
    .order_by(Task.id.desc())
    .limit(10)
)
```

3. **修改所有 Task/Trace/Adr 查询端点**
- `/api/v1/tasks/{id}/dag-tree`
- `/api/v1/tasks/{id}/generate-adr`
- `/api/v1/containers`
- `/api/v1/tasks/{id}/logs`

所有查询必须添加 `.where(Model.tenant_id == api_key.tenant_id)`

4. **添加 API 层隔离测试**
在 `test_tenant_isolation.py` 中添加：
```python
async def test_api_list_projects_tenant_filter():
    """Tenant B 无法通过 API 看到 Tenant A 的项目"""
    # 使用 Tenant B 的 Key 请求 /api/v1/projects
    # 验证返回列表仅包含 tenant_id=2 的项目
```

---

## 状态更新

**Sprint 19 状态**: `[!]` 打回

---

**Evaluator 签名**: Sprint 19 QA 评审打回 (5.00/10) - P0 安全漏洞