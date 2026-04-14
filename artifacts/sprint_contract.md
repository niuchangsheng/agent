# Sprint 13 验收合同：系统监控仪表盘

## 合同签署方
- **需求方**: product_spec.md Feature 12 (Sprint 13)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### Feature 12: 系统监控仪表盘 (System Monitoring Dashboard)
- **用户故事**: As a 运维工程师，I want 实时查看系统健康指标（CPU、内存、队列长度、响应延迟），so that 及时发现并处理性能瓶颈。
- **验收标准**:
  - Given 系统已运行 1 小时
  - When 运维打开监控仪表盘
  - Then 应显示：当前并发任务数、队列等待数、平均响应延迟 (P50/P95)、内存使用量、Redis 连接状态。
  - Given 某项指标超过阈值（如队列长度 > 100）
  - When 监控轮询时
  - Then 应以视觉警告（橙色/红色）高亮异常指标。

### 后端交付物

1. **指标采集器** (`app/metrics.py`):
   - 采集当前并发任务数（RUNNING 状态任务）
   - 采集队列等待数（QUEUED 状态任务）
   - 采集内存使用量（进程 RSS）
   - 采集 Redis 连接状态
   - 计算响应延迟 P50/P95（基于审计日志 duration_ms）

2. **监控 SSE 端点**:
   - `GET /api/v1/metrics/stream` - SSE 流式推送监控指标
   - 10 秒更新频率（限流）

3. **监控快照 API**:
   - `GET /api/v1/metrics` - 返回当前监控指标快照

4. **数据模型扩展**:
   - `SystemMetrics` 响应模型包含：
     - `concurrent_tasks` - 并发任务数
     - `queued_tasks` - 队列等待数
     - `latency_p50_ms` - P50 延迟（毫秒）
     - `latency_p95_ms` - P95 延迟（毫秒）
     - `memory_mb` - 内存使用量（MB）
     - `redis_connected` - Redis 连接状态
     - `queue_status` - 队列详细状态
     - `threshold_exceeded` - 超出阈值的指标列表

### 前端交付物

1. **监控仪表盘组件** (`src/components/MetricsDashboard.tsx`):
   - 实时显示并发任务数、队列等待数
   - 显示 P50/P95 延迟
   - 显示内存使用量
   - 显示 Redis 连接状态（绿色=正常，红色=断开）
   - 阈值告警视觉（橙色/红色高亮异常指标）
   - 10 秒自动刷新（SSE 或轮询）

2. **路由集成**:
   - 在 Dashboard 中添加监控仪表盘入口或直接集成

## 验收测试清单

### 后端指标采集测试
- [ ] `test_metrics_collector_concurrent_tasks` - 并发任务数统计正确
- [ ] `test_metrics_collector_queued_tasks` - 队列等待数统计正确
- [ ] `test_metrics_collector_memory` - 内存使用量采集正确
- [ ] `test_metrics_collector_redis_status` - Redis 连接状态检测正确
- [ ] `test_metrics_latency_percentile` - P50/P95 延迟计算正确

### 后端 API 测试
- [ ] `test_metrics_snapshot_api` - 监控快照 API 返回完整指标
- [ ] `test_metrics_stream_sse` - SSE 流式推送正常
- [ ] `test_metrics_stream_rate_limit` - SSE 限流 10 秒/次

### 前端组件测试
- [ ] `test_metrics_dashboard_renders` - 仪表盘组件渲染正常
- [ ] `test_metrics_dashboard_threshold_alert` - 阈值告警视觉正确
- [ ] `test_metrics_dashboard_redis_status` - Redis 状态显示正确

### 集成测试
- [ ] `test_metrics_full_lifecycle` - 监控指标随任务执行动态更新

## 技术约束

1. **性能影响**:
   - 指标采集不应显著影响主业务性能（目标 < 10ms 开销）
   - 指标采集频率限流至 10 秒/次

2. **阈值定义**:
   - 队列长度 > 100 → 警告
   - P95 延迟 > 1000ms → 警告
   - 内存 > 1024MB → 警告
   - Redis 断开 → 严重警告

3. **YAGNI 原则**:
   - 不实现复杂的时序数据库存储
   - 不实现历史趋势图表（仅显示当前值）

## 完成定义

- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-12 的测试
- [ ] handoff.md 更新完成
- [ ] ADR-013 决策记录创建（如有技术选型）

## 交付文件清单

- [ ] `src/backend/app/metrics.py` - 指标采集器（新增）
- [ ] `src/backend/app/main.py` - 监控 API 端点扩展
- [ ] `src/backend/tests/test_metrics.py` - 指标采集测试（新增）
- [ ] `src/frontend/src/components/MetricsDashboard.tsx` - 监控仪表盘组件（新增）
- [ ] `src/frontend/tests/MetricsDashboard.test.tsx` - 仪表盘组件测试（新增）
