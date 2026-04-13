# Sprint 12 验收合同：任务 ETA 预测 + 优先级

## 合同签署方
- **需求方**: product_spec.md Feature 11 + Feature 13 (Sprint 12)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### Feature 11: 任务进度 ETA 预测 (ETA Prediction)
- **用户故事**: As a 任务提交者，I want 看到长时任务的预计完成时间 (ETA)，so that 合理安排等待时间并在完成后返回。
- **验收标准**:
  - Given 一个长时任务已执行 50% 进度，耗时 30 秒
  - When 用户查看任务详情
  - Then 应显示预计剩余时间和预计完成时间点（如 "预计完成时间：2026-04-14 15:30，剩余约 30 秒"）
  - Given 任务进度更新
  - When ETA 计算时
  - Then 应使用移动平均算法平滑瞬时波动，避免 ETA 大幅跳变

### Feature 13: 任务优先级与插队 (Task Priority & Preemption)
- **用户故事**: As a 团队管理者，I want 为紧急任务设置高优先级使其插队执行，so that 关键任务可以绕过队列等待立即处理。
- **验收标准**:
  - Given 队列中有 5 个普通优先级任务等待
  - When 提交一个高优先级任务
  - Then 高优先级任务应立即插入队首，下一个空闲 Worker 优先执行它
  - Given 两个相同优先级的任务
  - When 队列调度时
  - Then 应遵循 FIFO 原则，先提交的先执行

### 后端交付物

1. **数据模型扩展**:
   - `Task` 模型新增字段:
     - `estimated_remaining_seconds` - 预计剩余时间（秒）
     - `estimated_completion_at` - 预计完成时间点

2. **ETA 计算器**:
   - 移动平均算法（至少 3 个样本点）
   - 少于 3 次进度更新时显示 null 或"计算中"
   - 进度 100% 时 ETA 归零

3. **优先级队列**:
   - 队列按 `priority DESC, created_at ASC` 排序
   - 高优先级任务插队逻辑
   - 现有 InMemoryQueue 和 RedisQueue 均需支持

4. **API 端点**:
   - `GET /api/v1/tasks/{task_id}` - 返回任务详情包含 ETA
   - `PUT /api/v1/tasks/{task_id}/priority` - 更新任务优先级

### 前端交付物
- 任务进度组件显示 ETA（可选，本期聚焦后端）

## 验收测试清单

### ETA 预测测试
- [ ] `test_eta_calculator_moving_average` - 移动平均计算正确
- [ ] `test_eta_calculator_insufficient_samples` - 样本不足时返回 null
- [ ] `test_eta_calculator_task_complete` - 任务完成时 ETA 归零
- [ ] `test_eta_api_returns_eta` - 任务 API 返回 ETA 字段

### 优先级队列测试
- [ ] `test_priority_queue_ordering` - 高优先级先出队
- [ ] `test_priority_fifo_same_priority` - 同优先级 FIFO 顺序
- [ ] `test_priority_preemption` - 高优先级插队
- [ ] `test_priority_update` - 任务优先级可更新

### 集成测试
- [ ] `test_task_with_eta_full_lifecycle` - 任务完整生命周期 ETA 更新
- [ ] `test_priority_queue_with_mixed_priorities` - 混合优先级队列调度

### 回归测试 (Sprint 7/9)
- [ ] `test_queue_basic_functionality` - 队列基础功能正常
- [ ] `test_task_progress_update` - 任务进度更新正常

## 技术约束

1. **移动平均算法**:
   - 使用最近 3-5 个进度样本
   - 避免瞬时波动导致 ETA 跳变

2. **性能影响**:
   - ETA 计算不应显著影响请求延迟（目标 < 5ms 开销）

3. **YAGNI 原则**:
   - 不实现复杂的机器学习预测
   - 不实现优先级饥饿问题处理（限制高优先级比例）

## 完成定义

- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-11 的测试
- [ ] handoff.md 更新完成
- [ ] ADR-012 决策记录创建（如有技术选型）

## 交付文件清单

- [ ] `src/backend/app/models.py` - Task 模型扩展 ETA 字段
- [ ] `src/backend/app/queue/base.py` - 优先级队列接口
- [ ] `src/backend/app/queue/in_memory_queue.py` - 优先级队列实现
- [ ] `src/backend/app/queue/redis_queue.py` - Redis 优先级队列
- [ ] `src/backend/app/eta.py` - ETA 计算器（新增）
- [ ] `src/backend/tests/test_eta.py` - ETA 预测测试
- [ ] `src/backend/tests/test_priority_queue.py` - 优先级队列测试
