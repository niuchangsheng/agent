# Sprint 9 验收合同：Redis 队列持久化

## 合同签署方
- **需求方**: product_spec.md Feature 8 (Sprint 9)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### 后端交付物

1. **数据模型扩展**:
   - `Task` 模型新增字段:
     - `priority` - 优先级 (0-10, 默认 0)
     - `created_at` - 创建时间
     - `updated_at` - 更新时间

2. **队列实现**:
   - `BaseQueue` - 队列抽象基类
   - `RedisQueue` - Redis 持久化队列实现
   - `InMemoryQueue` - 内存队列（降级模式）

3. **Redis Key 设计**:
   - `seca:queue:pending` - Sorted Set (优先级 + 时间排序)
   - `seca:queue:running` - Hash (运行中任务)
   - `seca:queue:task:{id}` - Hash (任务详情)

4. **配置**:
   - `REDIS_URL` 环境变量支持
   - Redis 连接超时配置

### API 端点 (保持不变)
- 现有队列 API 端点兼容，无需修改接口

## 验收测试清单

### TDD 测试用例 (必须全部通过)

#### Redis 队列核心测试
- [ ] `test_redis_enqueue_adds_to_sorted_set` - 入队添加到 Sorted Set
- [ ] `test_redis_dequeue_removes_highest_priority` - 出队取出最高优先级
- [ ] `test_redis_task_persistence` - 任务持久化到 Redis Hash
- [ ] `test_redis_progress_update_persists` - 进度更新持久化
- [ ] `test_redis_queue_status` - 队列状态查询

#### 崩溃恢复测试
- [ ] `test_recovery_restores_pending_tasks` - 恢复待执行任务
- [ ] `test_recovery_requeues_running_tasks` - 运行中任务重新入队
- [ ] `test_recovery_ignores_completed_tasks` - 已完成任务不恢复

#### 降级模式测试
- [ ] `test_fallback_to_memory_on_redis_unavailable` - Redis 不可用时降级内存队列
- [ ] `test_warning_logged_on_fallback` - 降级时记录警告日志
- [ ] `test_memory_queue_functions_without_redis` - 内存队列功能正常

#### 边界测试
- [ ] `test_empty_queue_dequeue_returns_none` - 空队列出队返回 None
- [ ] `test_same_priority_fifo_order` - 相同优先级遵循 FIFO
- [ ] `test_invalid_priority_rejected` - 无效优先级被拒绝

## 技术约束

1. **Redis 依赖**:
   - 使用 `redis-py` 异步客户端 `aredis` 或 `redis.asyncio`
   - 不阻塞服务启动（连接失败时降级）

2. **YAGNI 原则**:
   - MVP 仅支持单机 Redis
   - 不支持 Redis Cluster
   - 不实现 Redis Sentinel 高可用

3. **兼容性**:
   - 保持现有 API 端点不变
   - 队列接口抽象化，支持多实现

## 完成定义

- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-8 的测试
- [ ] handoff.md 更新完成
- [ ] ADR-009 决策记录创建

## 交付文件清单

- [ ] `src/backend/app/queue/__init__.py`
- [ ] `src/backend/app/queue/base.py`
- [ ] `src/backend/app/queue/redis_queue.py`
- [ ] `src/backend/app/queue/in_memory_queue.py`
- [ ] `src/backend/tests/test_redis_queue.py`
- [ ] `artifacts/decisions/ADR-009.md`
