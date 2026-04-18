# Sprint 17 验收合同：Docker 运维增强

## 合同签署方
- **需求方**: product_spec.md Feature 18 + Feature 19 + Feature 20 (Sprint 17)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### Feature 18: Docker 沙箱配置管理 (Docker Sandbox Configuration)
- **用户故事**: As a 系统管理员，I want 通过 Web 界面配置 Docker 沙箱的默认资源限制（内存、CPU、超时、进程数），so that 无需修改配置文件或重启服务即可调整沙箱行为。
- **验收标准**:
  - Given 系统已启用 Docker 沙箱
  - When 管理员访问配置管理页面的"Docker 沙箱"标签页
  - Then 应显示当前配置：内存限制 (MB)、CPU 限制 (核数)、执行超时 (秒)、最大并发容器数。
  - Given 管理员修改配置并保存
  - When 配置提交后
  - Then 应立即生效于新提交的任务，已有运行中容器不受影响。
  - Given 配置值非法（如内存 < 64MB 或 > 4GB）
  - When 保存时
  - Then 应拒绝保存并显示具体错误原因。

### Feature 19: Docker 容器资源监控 (Container Resource Monitoring)
- **用户故事**: As a 运维工程师，I want 实时查看 Docker 容器的资源使用量（CPU 百分比、内存 MB、网络 IO），so that 及时发现资源瓶颈或异常消耗。
- **验收标准**:
  - Given 有 3 个 Docker 容器正在运行
  - When 用户访问监控仪表盘的"容器资源"标签页
  - Then 应以卡片或表格形式显示每个容器的：容器 ID、所属任务、CPU 使用率%、内存使用量 MB、网络收发字节、运行时长。
  - Given 某容器 CPU 使用率超过 90% 持续 10 秒
  - When 监控轮询时
  - Then 应以橙色警告高亮该容器，并在日志中记录事件。
  - Given 容器执行完成或被终止
  - When 刷新监控视图
  - Then 该容器应从运行列表中移除，并可在"历史容器"中查看最终统计。

### Feature 20: Docker 日志增强与聚合 (Docker Log Aggregation)
- **用户故事**: As a 开发者，I want 查看 Docker 沙箱内的完整日志（包括标准输出、标准错误、容器启动/停止事件），so that 调试任务执行问题。
- **验收标准**:
  - Given 一个 Docker 容器已执行完成
  - When 用户访问任务详情的"容器日志"标签页
  - Then 应显示：容器启动时间、Pull 镜像日志、stdout 输出、stderr 输出、退出码、容器停止时间。
  - Given 日志超过 1000 行
  - When 加载日志时
  - Then 应默认显示最后 100 行，并提供"查看全部"按钮和按级别筛选（INFO/WARN/ERROR）。
  - Given 容器正在运行
  - When 查看日志
  - Then 应以流式方式实时追加新日志（SSE 或轮询）。

## 后端交付物

1. **Docker 配置模型** (`src/backend/app/models/docker_config.py`):
   - DockerConfig 表：memory_limit, cpu_limit, timeout, max_containers
   - CRUD API：GET/PUT /api/docker-config

2. **容器监控服务** (`src/backend/app/services/container_monitor.py`):
   - 获取容器 stats：CPU%、内存 MB、网络 IO、运行时长
   - 阈值检测：CPU > 90% 持续 10 秒记录事件
   - 历史容器统计

3. **Docker 日志服务** (`src/backend/app/services/docker_logger.py`):
   - 获取容器日志：stdout、stderr、启动/停止事件
   - 分页支持：默认最后 100 行
   - 级别筛选：INFO/WARN/ERROR

4. **API 端点** (`src/backend/app/api/docker.py`):
   - GET /api/docker-config - 获取 Docker 配置
   - PUT /api/docker-config - 更新 Docker 配置
   - GET /api/containers - 获取运行中容器列表
   - GET /api/containers/{container_id}/stats - 获取容器资源统计
   - GET /api/containers/{container_id}/logs - 获取容器日志
   - GET /api/containers/history - 获取历史容器统计

## 前端交付物

1. **Docker 配置组件** (`src/frontend/src/components/DockerConfigPanel.tsx`):
   - 配置表单：内存限制、CPU 限制、超时时间、最大并发数
   - 合法性校验：内存范围 64MB-4GB
   - 保存按钮、错误提示

2. **容器监控组件** (`src/frontend/src/components/ContainerMonitor.tsx`):
   - 容器列表卡片/表格
   - 实时指标显示（CPU%、内存 MB、网络 IO）
   - 阈值告警视觉（橙色/红色高亮）
   - 刷新按钮

3. **Docker 日志组件** (`src/frontend/src/components/DockerLogViewer.tsx`):
   - 日志显示区域
   - 分页控制（默认最后 100 行）
   - 级别筛选器（ALL/INFO/WARN/ERROR）
   - 实时流式追加

## 验收测试清单

### 后端单元测试
- [ ] `test_docker_config_get` - 获取 Docker 配置成功
- [ ] `test_docker_config_update` - 更新 Docker 配置成功
- [ ] `test_docker_config_validation_rejects_low_memory` - 拒绝内存 < 64MB
- [ ] `test_docker_config_validation_rejects_high_memory` - 拒绝内存 > 4GB
- [ ] `test_container_monitor_get_stats` - 获取容器统计成功
- [ ] `test_container_monitor_threshold_alert` - CPU 阈值告警触发
- [ ] `test_docker_logger_get_logs` - 获取容器日志成功
- [ ] `test_docker_logger_pagination` - 日志分页正确（默认 100 行）
- [ ] `test_docker_logger_level_filter` - 日志级别筛选正确

### 集成测试
- [ ] `test_docker_config_applies_to_new_tasks` - 配置更新后新任务生效
- [ ] `test_container_monitor_real_time_update` - 容器监控实时更新
- [ ] `test_docker_logs_streaming` - Docker 日志流式追加

### 前端测试
- [ ] `DockerConfigPanel renders current config` - 配置面板显示当前配置
- [ ] `DockerConfigPanel validates memory range` - 内存范围验证
- [ ] `ContainerMonitor displays container stats` - 容器监控显示统计
- [ ] `ContainerMonitor highlights high cpu` - 高 CPU 告警高亮
- [ ] `DockerLogViewer paginates logs` - 日志视图分页
- [ ] `DockerLogViewer filters by level` - 日志级别筛选

### 回归测试
- [ ] 不破坏现有 Sprint 1-16 的测试
- [ ] Docker 沙箱执行流程保持不变
- [ ] 配置更新不影响运行中容器

## 技术约束

1. **技术栈**:
   - 后端：FastAPI + SQLModel + pytest
   - 前端：React + TypeScript + Vite + Vitest
   - Docker SDK：docker-py 或 docker CLI

2. **性能要求**:
   - 容器监控 API 响应 < 200ms
   - 日志加载 < 500ms（1000 行以内）
   - 配置更新立即生效（无需重启）

3. **YAGNI 原则**:
   - 不实现多节点 Docker 集群管理
   - 不实现日志全文搜索
   - 不实现自定义告警规则

## 完成定义

- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-16 的测试
- [ ] handoff.md 更新完成
- [ ] ADR 决策记录创建（如有技术选型）

## 交付文件清单

### 后端
- [ ] `src/backend/app/models/docker_config.py` - Docker 配置模型
- [ ] `src/backend/app/services/container_monitor.py` - 容器监控服务
- [ ] `src/backend/app/services/docker_logger.py` - Docker 日志服务
- [ ] `src/backend/app/api/docker.py` - Docker API 端点
- [ ] `src/backend/tests/test_docker_config.py` - Docker 配置测试
- [ ] `src/backend/tests/test_container_monitor.py` - 容器监控测试
- [ ] `src/backend/tests/test_docker_logger.py` - Docker 日志测试

### 前端
- [ ] `src/frontend/src/components/DockerConfigPanel.tsx` - 配置面板
- [ ] `src/frontend/src/components/ContainerMonitor.tsx` - 容器监控
- [ ] `src/frontend/src/components/DockerLogViewer.tsx` - 日志视图
- [ ] `src/frontend/src/tests/DockerConfigPanel.test.tsx` - 配置面板测试
- [ ] `src/frontend/src/tests/ContainerMonitor.test.tsx` - 容器监控测试
- [ ] `src/frontend/src/tests/DockerLogViewer.test.tsx` - 日志视图测试
