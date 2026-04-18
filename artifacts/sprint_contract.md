# Sprint 17.5 验收合同：任务提交界面

## 合同签署方
- **需求方**: product_spec.md Sprint 17.5 (Feature 0 P0 核心入口补齐)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能概述
实现 TaskSubmitPanel 组件，作为 SECA 系统的核心入口，让用户能够通过 Web 界面提交新任务。

---

## 验收测试清单

### P0 必修项

#### 前端单元测试 (`src/frontend/tests/TaskSubmitPanel.test.tsx`) - 8 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `renders all form elements` | 渲染项目选择器、目标输入框、优先级选择器、提交按钮 | [ ] |
| `displays projects from API` | 项目选择器显示 API 返回的项目列表 | [ ] |
| `validates required fields` | 空目标输入时显示错误提示 | [ ] |
| `validates objective length` | 目标 > 500 字符时显示长度警告 | [ ] |
| `submits task successfully` | 提交成功后调用 onTaskCreated callback | [ ] |
| `handles API error gracefully` | API 错误时显示错误消息 | [ ] |
| `sends API key in headers` | 请求携带 X-API-Key header | [ ] |
| `disables submit when no API key` | 无 API Key 时禁用提交按钮并显示提示 | [ ] |

#### 边界测试覆盖

| 边界场景 | 验收标准 | 状态 |
|----------|----------|------|
| 空项目列表 | 显示"请先创建项目"提示 | [ ] |
| 目标长度超限 | 显示警告但不阻止提交 | [ ] |
| 优先级范围 | 默认 0，可选 0-10 | [ ] |
| 提交按钮状态 | 无 API Key / 无项目时禁用 | [ ] |
| 双击提交防抖 | 提交过程中按钮禁用 | [ ] |

---

## UI 设计规范

### Glassmorphism 风格一致性
- 容器: `backdrop-blur-md bg-slate-900/50 border-cyan-500/30 rounded-xl shadow-2xl`
- 输入框: `bg-slate-800/50 border-slate-700 rounded-lg`
- 按钮: `bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700`
- 错误提示: `bg-red-900/30 border-red-500/50 text-red-300`

### 响应式布局
- 项目选择器: 宽度 100%
- 目标输入框: textarea 最小高度 100px
- 优先级选择器: 使用 PrioritySelector 组件复用

---

## 技术实现要求

### API 集成
- **GET /api/v1/projects**: 获取项目列表
- **POST /api/v1/tasks**: 提交新任务
  - 请求体: `{ project_id: number, raw_objective: string, priority?: number }`

### 状态管理
- `projects`: 项目列表数组
- `selectedProjectId`: 当前选中项目 ID
- `objective`: 目标输入文本
- `priority`: 优先级值 (0-10)
- `loading`: 提交中状态
- `error`: 错误消息

### 组件 Props
```typescript
interface TaskSubmitPanelProps {
  onTaskCreated?: (task: Task) => void;  // 提交成功回调
}
```

---

## 完成定义

- [ ] 所有前端测试用例编写完成并通过 (8 tests)
- [ ] Glassmorphism 风格与其他组件一致
- [ ] 表单验证逻辑完整
- [ ] API Key 状态检测正常
- [ ] 回归测试：不破坏 Sprint 1-17 的功能
- [ ] TypeScript 编译无错误
- [ ] handoff.md 更新完成

---

## 技术备注

### 复用现有组件
- **PrioritySelector**: Sprint 15 已实现，直接复用
- **API Key 获取**: 使用 `localStorage.getItem('api_key')`

### 用户旅程闭环
提交成功后应:
1. 清空表单
2. 触发 onTaskCreated callback
3. 可跳转到 TaskQueueDashboard 查看队列状态

---

**签署时间**: 2026-04-18
**Generator 签名**: Sprint 17.5 开发启动