# Sprint 22 验收合同：租户选择器 UI — TD-004 (P1)

## 合同签署方
- **需求方**: handoff.md TD-004 (P1 优先级)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能概述
本 Sprint 实现前端租户选择器 UI，让用户能够：
1. 查看当前所属租户信息（名称、配额）
2. 在多租户环境下切换租户（如果有权限）
3. 显示租户配额使用情况

---

## Part A: TenantInfo 组件

### 前端单元测试 (`src/frontend/src/components/__tests__/TenantInfo.test.tsx`) - 4 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_tenant_info_displays_name` | 显示租户名称 | [ ] |
| `test_tenant_info_displays_quota` | 显示配额信息（任务数、存储） | [ ] |
| `test_tenant_info_fetches_from_api` | 从 `/api/v1/tenants/me` 获取数据 | [ ] |
| `test_tenant_info_handles_error` | API 错误时显示友好提示 | [ ] |

### TenantInfo 设计要点

```tsx
interface TenantInfoProps {
  apiKey: string;
}

interface Tenant {
  id: number;
  name: string;
  slug: string;
  quota_tasks: number;
  quota_storage_mb: number;
  quota_api_calls: number;
  is_active: boolean;
}
```

- 位置: 右上角或 SidePanel 顶部
- 显示: 租户名称 + 配额使用率（如有数据）
- 样式: Glassmorphism 风格，青色边框

---

## Part B: TenantSelector 下拉组件

### 前端单元测试 (`src/frontend/src/components/__tests__/TenantSelector.test.tsx`) - 3 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_selector_dropdown_visible` | 点击后显示下拉列表 | [ ] |
| `test_selector_lists_available_tenants` | 显示可切换的租户列表 | [ ] |
| `test_selector_switch_updates_state` | 切换租户后更新当前租户状态 | [ ] |

### TenantSelector 设计要点

- 如果用户只有一个租户：只显示 TenantInfo
- 如果用户有多个租户：显示下拉选择器
- 切换租户：更新 localStorage 中的 tenant_id

---

## Part C: App.tsx 集成

### 前端单元测试 (`src/frontend/src/__tests__/App.tenant.test.tsx`) - 2 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_tenant_info_in_header` | 右上角显示租户信息 | [ ] |
| `test_tenant_switch_refreshes_data` | 切换租户后刷新任务列表 | [ ] |

---

## 实施步骤

### Step 1: 🔴 Red - 编写测试文件
创建测试文件:
- `TenantInfo.test.tsx` (4 tests)
- `TenantSelector.test.tsx` (3 tests)
- `App.tenant.test.tsx` (2 tests)

**预期结果**: 所有测试失败 (组件未创建)

### Step 2: 🟢 Green - 实现组件
创建组件:
- `TenantInfo.tsx`
- `TenantSelector.tsx`
- 修改 `App.tsx` 集成租户显示

### Step 3: 🔵 Refactor - 回归测试
- 运行前端 Vitest 全量测试
- 确保现有组件未破坏

---

## 完成定义

- [x] TenantInfo 测试全部通过 (4 tests)
- [x] TenantSelector 测试全部通过 (3 tests)
- [x] App.tsx 集成完成
- [x] 前端全量测试通过 (110 tests)
- [x] handoff.md 更新完成

## 测试证据

```bash
$ npm test
 Test Files  20 passed (20)
      Tests  110 passed (110)
```

## 实现内容

### TenantInfo 组件
- 显示租户名称和配额信息
- 从 `/api/v1/tenants/me` 获取数据
- 错误处理和加载状态

### TenantSelector 组件
- 多租户下拉选择器
- 点击切换租户
- 更新 localStorage tenant_id

## Generator 签名
**Generator**: Sprint 22 租户选择器 UI 完成 ✅ - 110 tests passed