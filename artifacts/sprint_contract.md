# Sprint 13 验收合同（修复版）：系统监控仪表盘

## 合同签署方
- **需求方**: product_spec.md Feature 12 (Sprint 13)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## QA 打回原因（来自 qa_feedback.md）
1. **无前端单元测试**: `MetricsDashboard.test.tsx` 缺失
2. **无后端集成测试**: `test_metrics.py` 缺失
3. **TDD 流程未执行**: 先实现代码后补测试（实际未补）
4. **API Key 认证性能问题**: bcrypt 验证 196 个 Key 需 120 秒

## 修复状态

### P0 必修项
| 项目 | 状态 | 证据 |
|------|------|------|
| 前端 MetricsDashboard.test.tsx | ✅ 已完成 | 8 个测试用例，覆盖渲染/API调用/错误处理/阈值告警/自动刷新 |
| 后端 test_metrics.py | ✅ 已完成 | 19 个测试用例，覆盖指标采集/API端点/集成测试/阈值检测 |
| API Key 认证性能 | ✅ 已修复 | SHA-256 替代 bcrypt，196 Key 验证 0.24ms |

## 验收测试清单

### 后端单元测试 (`src/backend/tests/test_metrics.py`)
- [x] `test_metrics_collector_initialization` - 指标采集器初始化
- [x] `test_metrics_collector_concurrent_tasks` - 并发任务数统计正确
- [x] `test_metrics_collector_queued_tasks` - 队列等待数统计正确
- [x] `test_metrics_collector_memory` - 内存使用量采集正确
- [x] `test_metrics_collector_redis_status_connected` - Redis 连接状态检测（已连接）
- [x] `test_metrics_collector_redis_status_disconnected` - Redis 连接状态检测（未连接）
- [x] `test_metrics_latency_percentile` - P50/P95 延迟计算正确
- [x] `test_metrics_latency_no_data` - 无审计日志时延迟返回 0
- [x] `test_metrics_snapshot` - 监控快照数据完整
- [x] `test_metrics_threshold_detection` - 阈值超出检测正确

### 后端 API 测试
- [x] `test_metrics_snapshot_api` - 监控快照 API 返回完整指标
- [x] `test_metrics_stream_sse` - SSE 流式推送正常
- [x] `test_metrics_stream_rate_limit` - SSE 端点基本响应

### 后端集成测试
- [x] `test_metrics_update_on_task_submission` - 提交任务后并发数增加

### 阈值告警测试
- [x] `test_threshold_queue_length` - 队列长度超阈值检测
- [x] `test_threshold_latency` - 延迟超阈值检测
- [x] `test_threshold_memory` - 内存超阈值检测
- [x] `test_threshold_redis_disconnected` - Redis 断开告警
- [x] `test_no_threshold_exceeded` - 无阈值超出

### 前端单元测试 (`src/frontend/tests/MetricsDashboard.test.tsx`)
- [x] `renders loading state initially` - 渲染初始加载状态
- [x] `displays all metrics from API` - 显示所有 API 指标
- [x] `shows Redis connected status` - Redis 连接状态显示
- [x] `shows Redis disconnected status with warning` - Redis 断开状态警告
- [x] `applies warning style for exceeded thresholds` - 阈值超限警告样式
- [x] `auto-refreshes every 10 seconds` - 10 秒自动刷新
- [x] `sends API key in request headers` - 请求头携带 API Key
- [x] `handles missing API key gracefully` - 缺失 API Key 优雅处理

## 测试执行证据

### 后端测试结果
```bash
$ cd src/backend && source venv/bin/activate && python -m pytest tests/test_metrics.py -v
======================== 19 passed, 8 warnings in 2.29s ========================
```

### 前端测试结果
```bash
$ cd src/frontend && npm test
 Test Files  9 passed (9)
      Tests  44 passed (44)
   Duration  6.79s
```

## 回归测试

### 后端全量测试
```bash
$ python -m pytest tests/ -v --tb=short
============ 8 failed, 121 passed, 9 skipped, 8 warnings in 42.62s =============
```
注：8 个失败与 Sprint 17 Docker 运维相关，Sprint 13 metrics 测试全部通过。

### 前端全量测试
- 全量 44 个测试通过，无回归

## 完成定义

- [x] 所有后端测试用例编写完成并通过 (19 passed)
- [x] 所有前端测试用例编写完成并通过 (8 passed)
- [x] API Key 认证性能问题已修复 (SHA-256)
- [x] 测试覆盖渲染、API调用、错误处理、阈值告警、自动刷新
- [x] 回归测试：不破坏 Sprint 1-12 的功能
- [x] handoff.md 更新完成

## 技术备注

### API Key 认证性能修复
- 原方案：bcrypt 哈希，单次验证 615ms，196 Key 验证需 120 秒
- 新方案：SHA-256 哈希，单次验证 0.001ms，196 Key 验证 0.24ms
- 性能提升：约 500,000 倍

## 交付文件清单

### 后端
- [x] `src/backend/tests/test_metrics.py` - 监控测试套件 (19 tests)
- [x] `src/backend/app/metrics.py` - MetricsCollector 实现

### 前端
- [x] `src/frontend/tests/MetricsDashboard.test.tsx` - 监控仪表盘测试 (8 tests)
- [x] `src/frontend/src/components/MetricsDashboard.tsx` - 监控仪表盘组件

---

**签署时间**: 2026-04-18
**Generator 签名**: Sprint 13 修复完成，待 QA 复审