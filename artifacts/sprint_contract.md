# Sprint 7 验收合同：异步任务队列

## 合同签署方
- **需求方**: product_spec.md Feature 6
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### 后端交付物
1. **数据模型扩展**: `Task` 表新增字段：
   - `progress_percent` - 进度百分比 (0-100)
   - `queue_position` - 队列位置
   - `worker_id` - 执行 Worker ID
   - `status_message` - 进度状态消息
   - `completed_at` - 完成时间
   - `started_at` - 开始执行时间

2. **任务队列管理器** (`app/task_queue.py`):
   - `TaskQueue` 类：管理待执行任务队列
   - 并发限制：默认 2 个并发槽位
   - Worker 崩溃恢复机制

3. **API 端点**:
   - `POST /api/v1/tasks/queue` - 提交任务到队列
   - `GET /api/v1/tasks/queue` - 查看队列状态
   - `DELETE /api/v1/tasks/queue/{task_id}` - 取消队列中的任务
   - `GET /api/v1/tasks/{task_id}/progress` - 获取任务进度
   - `PUT /api/v1/tasks/{task_id}/progress` - 更新任务进度
   - `POST /api/v1/tasks/{task_id}/complete` - 标记任务完成
   - `POST /api/v1/tasks/{task_id}/worker-crash` - 模拟 Worker 崩溃

### 前端交付物
1. **任务队列 Dashboard** (`TaskQueueDashboard.tsx`):
   - 队列状态展示（等待中/执行中）
   - 实时进度条（每 2 秒轮询）
   - 取消队列任务功能

2. **应用集成**:
   - 添加 Task Queue 标签页
   - 三标签页架构：Dashboard / Task Queue / Configuration

## 验收测试清单

### TDD 测试用例 (全部通过 ✅)

#### 后端测试 (10/10)
- [x] `test_queue_task_submission` - 任务提交到队列
- [x] `test_queue_concurrency_limit` - 2 并发限制下 3 任务正确调度
- [x] `test_queue_task_progress_update` - 任务进度更新
- [x] `test_queue_task_completion` - 任务完成后释放槽位
- [x] `test_queue_cancel_task` - 取消队列中任务
- [x] `test_queue_task_not_found_returns_404` - 任务不存在返回 404
- [x] `test_queue_cancel_non_existent_task` - 取消不存在任务失败
- [x] `test_queue_invalid_progress_value` - 无效进度值验证
- [x] `test_queue_worker_crash_recovery` - Worker 崩溃后任务重新入队
- [x] `test_queue_progress_real_time` - 进度实时更新验证

#### 前端测试 (6/6)
- [x] `应当渲染任务队列仪表板标题`
- [x] `应当显示队列概览统计`
- [x] `应当显示运行中任务进度条`
- [x] `应当能取消队列中任务`
- [x] `应当在队列为空时显示提示`
- [x] `应当显示刷新按钮`

## 测试结果汇总
- **后端测试**: 30/30 通过 (包含 Sprint 1-7 的回归测试)
- **前端测试**: 18/18 通过

## 完成定义
- [x] 所有测试用例编写完成 (Red)
- [x] 所有测试用例通过 (Green)
- [x] Lint 检查无警告
- [x] 不破坏现有 Sprint 1-6 的测试
- [x] handoff.md 更新完成

## 交付状态
✅ **Sprint 7 已完成，准备接受 QA 评审**
