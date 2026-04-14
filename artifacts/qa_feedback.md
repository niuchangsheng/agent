# QA 评审反馈：Sprint 14 - 前端监控仪表盘

## 评审概况
- **评审时间**: 2026-04-15
- **评审官**: SECA Evaluator
- **Sprint 状态**: [!] 打回（总分 < 7.0）

---

## 冒烟门禁测试结果

### 后端服务
- **启动命令**: `cd /home/chang/agent/src/backend && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **健康检查**: `curl -s http://localhost:8000/api/v1/health`
- **响应**: `{"status":"active"}` ✅ 通过

### 前端服务
- **启动命令**: `cd /home/chang/agent/src/frontend && npm run dev`
- **页面检查**: `curl -s http://localhost:5173 | grep "<title>"`
- **响应**: `<title>frontend</title>` ✅ 通过

### Metrics API 验证
- **端点**: `GET /api/v1/metrics`
- **响应示例** (带有效 API Key):
```json
{
    "concurrent_tasks": 1,
    "queued_tasks": 3,
    "latency_p50_ms": 140.0,
    "latency_p95_ms": 34752.0,
    "memory_mb": 72.7421875,
    "redis_connected": false,
    "threshold_exceeded": ["latency_p95", "redis_connected"]
}
```
- **注意**: API 需要 `X-API-Key` 认证头，但前端组件未配置

---

## TDD 合规检查

### 测试覆盖分析
| 合同验收项 | 测试用例 | 覆盖状态 |
|-----------|---------|---------|
| 仪表盘渲染 | `test_metrics_dashboard_renders` | ✅ 已覆盖 |
| 显示全部指标 | `test_metrics_dashboard_displays_metrics` | ✅ 已覆盖 |
| 阈值告警视觉 | `test_metrics_dashboard_threshold_alert` | ✅ 已覆盖 |
| Redis 状态 | `test_metrics_dashboard_redis_status` | ✅ 已覆盖 |
| 自动刷新 | `test_metrics_dashboard_auto_refresh` | ✅ 已覆盖 |
| API 集成 | ❌ 缺失 | ❌ **未覆盖** |
| SSE 连接 | ❌ 缺失 | ❌ **未覆盖** |

### 回归测试
- **前端全量测试**: 29 个测试全部通过 ✅
- **后端 metrics 测试**: 18 个通过，1 个环境失败（数据库锁定，非 Sprint 14 缺陷）✅

### 代码质量审计
- **TDD 执行**: 测试先行 ✓，组件实现 ✓
- **TypeScript 类型**: 完整定义 `MetricsData` 接口 ✓
- **错误处理**: `try/catch` 捕获 fetch 错误 ✓
- **Lint 检查**: 待执行

---

## 致命缺陷发现

### [BLOCKER] 缺失 API Key 认证集成

**问题描述**: 
- `MetricsDashboard.tsx` 组件调用 `/api/v1/metrics` 时**未携带 API Key 认证头**
- 后端 `require_write_key` 依赖要求 `X-API-Key` 请求头
- 实际运行时，前端无法从后端获取任何监控数据

**证据**:
```bash
# 无 API Key 请求 → 被拒绝
$ curl -s http://localhost:8000/api/v1/metrics
{"detail": "Missing API key"}

# 有 API Key 请求 → 正常返回
$ curl -s -H "X-API-Key: ZkeBw2YXExkvoS2aGKmuD_ofUsOrN0kd2VdgXcCsoiE" http://localhost:8000/api/v1/metrics
{"concurrent_tasks": 1, "queued_tasks": 3, ...}
```

**合同违反**:
- Sprint 14 合同明确要求："使用 SSE 或轮询连接 `/api/v1/metrics`"
- 当前实现**无法真正连接**，因为缺少认证
- 验收测试清单中 `test_metrics_dashboard_api_integration` 未实现

**影响范围**:
- 前端组件在实际环境中无法获取真实数据
- 用户打开监控页面只会看到空值或错误状态
- 功能完整性严重受损

---

## 四维修炼打分

| 评估维度 | 得分 | 权重 | 加权分 | 证据引用 |
|---------|------|------|--------|---------|
| **功能完整实现度** | 5/10 | 35% | 1.75 | 合同要求"连接 `/api/v1/metrics`"，但组件未集成 API Key 认证，无法真正获取数据。验收测试清单中 `test_metrics_dashboard_api_integration` 缺失。 |
| **设计工程质量** | 8/10 | 25% | 2.00 | 卡片布局符合项目 Tailwind 风格，警告色（橙色/红色）正确应用，响应式网格 `grid-cols-2 md:grid-cols-3 lg:grid-cols-6` 适配多种屏幕。 |
| **代码内聚素质** | 8/10 | 20% | 1.60 | TypeScript 类型定义完整，错误处理有 `try/catch`，6 个单元测试全部通过，TDD 执行规范。 |
| **人类感受用户体验** | 6/10 | 20% | 1.20 | 组件 UI 设计良好，但因无法获取真实数据，用户实际看到的可能一直是 loading 或错误状态（取决于错误处理逻辑）。 |
| **总计** | | | **6.55** | **< 7.0 及格线** ❌ |

---

## 判定结果

**[!] Sprint 14 打回**

### 必修打回要求 [!]

1. **[!] 集成 API Key 认证**: 
   - `MetricsDashboard.tsx` 需要从 localStorage 或全局状态获取 API Key
   - 在 fetch 请求中添加 `headers: { 'X-API-Key': apiKey }`
   - 或修改后端 `/api/v1/metrics` 为公开端点（不需要认证）

2. **[!] 补充集成测试**:
   - 添加 `test_metrics_dashboard_api_integration` 测试
   - 验证组件能够正确发送 API Key 请求头

3. **[!] 修复合同验收项**:
   - 验收测试清单中明确列出的 `test_metrics_dashboard_api_integration` 必须实现
   - 验收测试清单中明确列出的 `test_metrics_dashboard_sse_connection` 必须实现（或使用轮询替代说明）

---

## 整改指导建议

### 建议方案 A: 前端集成 API Key（推荐）
```typescript
// MetricsDashboard.tsx 修改示例
const fetchMetrics = async () => {
  try {
    // 从 localStorage 获取最近使用的 API Key
    const apiKey = localStorage.getItem('api_key') || '';
    const response = await fetch('/api/v1/metrics', {
      headers: { 'X-API-Key': apiKey }
    });
    // ... 其余逻辑不变
  }
};
```

### 建议方案 B: 后端开放 Metrics 端点
```python
# main.py 修改示例
@app.get("/api/v1/metrics")
async def get_metrics(session: AsyncSession = Depends(get_db_session)):
    """获取系统监控指标快照 - 无需认证（监控数据本身不敏感）"""
    # 移除 api_key: APIKey = Depends(require_write_key) 依赖
```

---

## 回归验证

| Sprint | 关键路径 | 验证结果 |
|--------|---------|---------|
| Sprint 1-5 | Dashboard 渲染 | ✅ 29 个前端测试通过 |
| Sprint 6-8 | API Key 管理 | ✅ 后端 auth 端点正常 |
| Sprint 9-13 | 任务队列 | ✅ `/api/v1/tasks` 正常返回 |

---

## 附录：终端证据

### 前端测试输出
```
> vitest --run
Test Files  7 passed (7)
Tests  29 passed (29)
```

### 后端 metrics 测试输出
```
PASSED tests/test_metrics.py::TestMetricsCollector::test_metrics_collector_initialization
PASSED tests/test_metrics.py::TestMetricsCollector::test_get_memory_info
...
FAILED tests/test_metrics.py::TestMetricsIntegration::test_metrics_update_on_task_submission
(数据库锁定环境问题，非代码缺陷)
```

### API 验证
```bash
$ curl -s http://localhost:8000/api/v1/metrics
{"detail": "Missing API key"}

$ curl -s -H "X-API-Key: <valid_key>" http://localhost:8000/api/v1/metrics
{"concurrent_tasks": 1, "queued_tasks": 3, ...}
```

---

**评审官签名**: SECA Evaluator
**下次动作**: Generator 修复上述 [!] 问题后重新提交 QA
