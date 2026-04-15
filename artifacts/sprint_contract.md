# Sprint 15 验收合同：ETA 显示 + 优先级选择器

## 合同签署方
- **需求方**: product_spec.md Feature 15 + Feature 16 (Sprint 15)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### Feature 15: ETA 显示组件 (ETA Display)
- **用户故事**: As a 任务提交者，I want 看到长时任务的预计完成时间 (ETA)，so that 合理安排等待时间并在完成后返回。
- **验收标准**:
  - Given 一个长时任务已执行 50% 进度，耗时 30 秒
  - When 用户查看任务详情
  - Then 应显示预计剩余时间和预计完成时间点（如 "剩余约 30 秒" 或 "预计 2026-04-13 15:30 完成"）。
  - Given 任务进度更新
  - When ETA 计算时
  - Then 应使用移动平均算法平滑瞬时波动，避免 ETA 大幅跳变。

### Feature 16: 优先级选择器 (Priority Selector)
- **用户故事**: As a 团队管理者，I want 为任务设置优先级 (0-10)，so that 重要任务可以优先执行。
- **验收标准**:
  - Given 用户创建新任务
  - When 选择优先级时
  - Then 应支持 0-10 范围选择，默认值为 0。
  - Given 任务已在队列中
  - When 用户调整优先级
  - Then 队列位置应相应更新，高优先级任务插队到前面。

### 前端交付物

1. **ETA 显示组件** (`src/components/ETADisplay.tsx` 或集成到现有组件):
   - 显示预计剩余时间（秒或分钟格式）
   - 显示预计完成时间点（绝对时间）
   - 进度少于 3 次更新时显示"计算中..."
   - 无 ETA 数据时显示"-"或隐藏

2. **优先级选择器组件** (`src/components/PrioritySelector.tsx`):
   - 支持 0-10 范围选择
   - 创建任务时可选择优先级
   - 已存在任务可调整优先级（调用 PUT API）
   - 高优先级视觉提示（如颜色区分）

3. **任务列表集成**:
   - 在任务列表/下拉选择中显示优先级
   - 在 Dashboard 或任务详情中显示 ETA

### 后端依赖（已完成 - Sprint 12/9）
- `GET /api/v1/tasks` - 任务列表（包含 priority, estimated_remaining_seconds, estimated_completion_at）
- `POST /api/v1/tasks` - 创建任务（支持 priority 参数）
- `PUT /api/v1/tasks/{task_id}/priority` - 更新任务优先级

## 验收测试清单

### 前端组件测试
- [x] `test_eta_display_shows_remaining_time` - ETA 显示剩余时间正确
- [x] `test_eta_display_shows_completion_time` - ETA 显示完成时间点正确
- [x] `test_eta_display_calculating` - 进度不足 3 次时显示"计算中..."
- [x] `test_priority_selector_renders_0_to_10` - 优先级选择器渲染 0-10 选项
- [x] `test_priority_selector_updates_on_change` - 优先级变更调用 API
- [x] `test_priority_selector_high_priority_visual` - 高优先级视觉提示正确

### 集成测试
- [x] `test_task_creation_with_priority` - 创建任务带优先级参数（后端已有）
- [x] `test_priority_update_api_call` - 优先级更新 API 调用正确
- [x] `test_eta_data_from_api` - ETA 数据从 API 正确获取（后端已有）

### 回归测试
- [x] 不破坏现有 Sprint 1-14 的测试（44/44 通过）

## 技术约束

1. **技术栈**:
   - React 18 + TypeScript + Vite
   - Vitest + React Testing Library 测试

2. **UI/UX**:
   - 优先级选择器使用滑动条或数字输入
   - 高优先级（≥7）使用橙色/红色视觉提示
   - ETA 时间格式友好（如 "约 2 分钟" 而非 "120 秒"）

3. **YAGNI 原则**:
   - 不实现 ETA 历史趋势图
   - 不实现优先级批量调整
   - 不实现优先级自动推荐

## 完成定义

- [x] 所有测试用例编写完成 (Red)
- [x] 所有测试用例通过 (Green) - 13/13 通过
- [x] Lint 检查无警告
- [x] 不破坏现有 Sprint 1-14 的测试 - 44/44 通过
- [x] handoff.md 更新完成
- [ ] ADR-015 决策记录创建（如有技术选型）

## 交付文件清单

- [x] `src/frontend/src/components/ETADisplay.tsx` - ETA 显示组件（新增）
- [x] `src/frontend/src/components/PrioritySelector.tsx` - 优先级选择器组件（新增）
- [x] `src/frontend/tests/ETADisplay.test.tsx` - ETA 组件测试（新增）
- [x] `src/frontend/tests/PrioritySelector.test.tsx` - 优先级选择器测试（新增）
- [x] `src/frontend/src/components/TaskQueueDashboard.tsx` - 集成 ETA 和优先级（修改）
