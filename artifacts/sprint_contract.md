# Sprint 14 验收合同：前端监控仪表盘

## 合同签署方
- **需求方**: product_spec.md Feature 14 (Sprint 14)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### Feature 14: 前端监控仪表盘 (Frontend Monitoring Dashboard)
- **用户故事**: As a 运维工程师，I want 在浏览器中直观查看系统监控指标和阈值告警，so that 无需通过 API 即可快速了解系统健康状态。
- **验收标准**:
  - Given 系统有 3 个并发任务和 5 个排队任务
  - When 用户打开监控页面
  - Then 应以卡片/图表形式显示各项指标，并自动每 10 秒刷新。
  - Given 队列长度超过 100 阈值
  - When 指标更新时
  - Then 相应指标卡片应变为橙色/红色警告色。

### 前端交付物

1. **监控仪表盘组件** (`src/components/MetricsDashboard.tsx`):
   - 使用 SSE 或轮询连接 `/api/v1/metrics/stream` 或 `/api/v1/metrics`
   - 显示并发任务数卡片
   - 显示队列等待数卡片
   - 显示 P50/P95 延迟卡片
   - 显示内存使用量卡片
   - 显示 Redis 连接状态指示器
   - 阈值告警视觉（超出阈值时卡片变橙/红色）
   - 自动刷新（10 秒间隔）

2. **路由集成**:
   - 在 App.tsx 或 Dashboard 中添加监控仪表盘路由或入口

### 后端依赖（已完成）
- `GET /api/v1/metrics` - 监控指标快照 API
- `GET /api/v1/metrics/stream` - SSE 流式推送

## 验收测试清单

### 前端组件测试
- [ ] `test_metrics_dashboard_renders` - 仪表盘组件渲染正常
- [ ] `test_metrics_dashboard_displays_metrics` - 显示全部指标（并发数、队列数、延迟、内存、Redis）
- [ ] `test_metrics_dashboard_threshold_alert` - 阈值告警视觉正确
- [ ] `test_metrics_dashboard_redis_status` - Redis 状态显示正确
- [ ] `test_metrics_dashboard_auto_refresh` - 自动刷新正常

### 集成测试
- [ ] `test_metrics_dashboard_api_integration` - 与后端 API 集成正常
- [ ] `test_metrics_dashboard_sse_connection` - SSE 连接建立正常

### 回归测试
- [ ] 不破坏现有 Sprint 1-13 的测试

## 技术约束

1. **技术栈**:
   - React 18 + TypeScript + Vite
   - Vitest + React Testing Library 测试

2. **性能影响**:
   - 组件首次渲染 < 100ms
   - SSE 连接建立 < 500ms

3. **YAGNI 原则**:
   - 不实现历史趋势图表（仅显示当前值）
   - 不实现指标导出功能

## 完成定义

- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-13 的测试
- [ ] handoff.md 更新完成
- [ ] ADR-014 决策记录创建（如有技术选型）

## 交付文件清单

- [ ] `src/frontend/src/components/MetricsDashboard.tsx` - 监控仪表盘组件（新增）
- [ ] `src/frontend/src/components/MetricsCard.tsx` - 指标卡片组件（可选复用）
- [ ] `src/frontend/tests/MetricsDashboard.test.tsx` - 仪表盘组件测试（新增）
- [ ] `src/frontend/src/App.tsx` - 路由集成（修改）
