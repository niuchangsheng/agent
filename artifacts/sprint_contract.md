# Sprint 17 验收合同（修复版）：Docker 运维增强

## 合同签署方
- **需求方**: product_spec.md Feature 18, 19, 20 (Sprint 17)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## QA 打回原因（来自 QA 评审报告）

| 问题 | 状态 | 修复计划 |
|------|------|----------|
| 前端 TypeScript 编译失败 | ✅ 已修复 | npx tsc --noEmit 无错误输出 |
| 测试数据库锁问题 | ❌ 未修复 | 需验证测试执行情况 |
| UI 组件无 Vitest 测试 | ❌ 待修复 | 需编写 3 个组件测试 |
| 边界测试缺失 | ❌ 待修复 | 补充边界条件测试 |
| 后端测试期望值错误 | ❌ 待修复 | 400 → 422（FastAPI 标准） |

---

## 验收测试清单

### P0 必修项

#### 前端单元测试 (`src/frontend/tests/`)

**DockerConfigPanel.test.tsx** (8 tests):
- [ ] `renders loading state initially` - 渲染初始加载状态
- [ ] `displays config from API` - 显示 API 返回的配置
- [ ] `validates memory limit range` - 内存范围验证提示
- [ ] `validates cpu limit range` - CPU 范围验证提示
- [ ] `validates timeout range` - 超时范围验证提示
- [ ] `saves config successfully` - 成功保存配置
- [ ] `handles API error gracefully` - API 错误处理
- [ ] `sends API key in headers` - 请求携带 API Key

**ContainerMonitor.test.tsx** (8 tests):
- [ ] `renders empty state when no containers` - 无容器时空状态
- [ ] `displays container stats from API` - 显示容器统计
- [ ] `shows CPU warning style for high usage` - CPU 高使用警告样式
- [ ] `shows memory warning style for high usage` - 内存高使用警告样式
- [ ] `formats bytes correctly` - 字节格式化正确
- [ ] `formats duration correctly` - 时长格式化正确
- [ ] `auto-refreshes on interval` - 定时自动刷新
- [ ] `handles missing API key gracefully` - 缺失 API Key 处理

**DockerLogViewer.test.tsx** (8 tests):
- [ ] `renders loading state initially` - 渲染初始加载状态
- [ ] `displays logs from API` - 显示 API 返回的日志
- [ ] `filters by level INFO` - INFO 级别筛选
- [ ] `filters by level ERROR` - ERROR 级别筛选
- [ ] `changes lines count` - 行数选择功能
- [ ] `shows truncated indicator` - 截断指示器
- [ ] `applies level color coding` - 级别颜色编码
- [ ] `handles missing API key gracefully` - 缺失 API Key 处理

#### 后端单元测试修复 (`src/backend/tests/test_docker_ops.py`)

- [ ] `test_docker_config_get` - ✅ 已通过
- [ ] `test_docker_config_update` - ✅ 已通过
- [ ] `test_docker_config_validation_rejects_low_memory` - ❌ 修复期望值 400 → 422
- [ ] `test_docker_config_validation_rejects_high_memory` - ❌ 修复期望值 400 → 422
- [ ] `test_container_monitor_get_stats` - ✅ 已通过
- [ ] `test_container_history` - ✅ 已通过
- [ ] `test_docker_logger_get_logs` - ✅ 已通过

#### 补充边界测试

**后端边界测试** (新增):
- [ ] `test_docker_config_validation_rejects_low_cpu` - CPU < 0.5 拒绝
- [ ] `test_docker_config_validation_rejects_high_cpu` - CPU > 4 拒绝
- [ ] `test_docker_config_validation_rejects_low_timeout` - timeout < 10 拒绝
- [ ] `test_docker_config_validation_rejects_high_timeout` - timeout > 300 拒绝
- [ ] `test_docker_config_validation_rejects_low_containers` - containers < 1 拒绝
- [ ] `test_docker_config_validation_rejects_high_containers` - containers > 10 拒绝

---

## 测试执行证据要求

### 前端测试结果
```bash
$ cd src/frontend && npm test
 Test Files  12+ passed (12+)
      Tests  69+ passed (69+)
```

### 后端测试结果
```bash
$ cd src/backend && source venv/bin/activate && python -m pytest tests/test_docker_ops.py -v
======================== 13+ passed ========================
```

---

## 完成定义

- [ ] 所有前端测试用例编写完成并通过 (24 tests)
- [ ] 所有后端测试修复并通过 (13 tests)
- [ ] 边界测试覆盖全部字段范围验证
- [ ] 回归测试：不破坏 Sprint 1-16 的功能
- [ ] TypeScript 编译无错误
- [ ] handoff.md 更新完成

---

## 技术备注

### FastAPI 验证响应码说明
- FastAPI 的 Pydantic 验证失败默认返回 **422 Unprocessable Entity**
- 测试期望 400 是错误理解，应修正为 422
- 参考：https://fastapi.tiangolo.com/tutorial/handling-errors/

### 前端组件 Glassmorphism 风格一致性
- DockerConfigPanel: `backdrop-blur-md bg-slate-900/50 border-cyan-500/30`
- ContainerMonitor: `backdrop-blur-md bg-slate-900/50 border-cyan-500/30`
- DockerLogViewer: `backdrop-blur-md bg-slate-900/50 border-purple-500/30`

---

**签署时间**: 2026-04-18
**Generator 签名**: Sprint 17 修复开发启动