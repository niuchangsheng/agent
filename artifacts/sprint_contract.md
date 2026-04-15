# Sprint 16 验收合同：Docker 沙箱隔离

## 合同签署方
- **需求方**: product_spec.md Feature 17 (Sprint 16)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### Feature 17: Docker 沙箱隔离 (Docker Sandbox Isolation)
- **用户故事**: As a 系统安全官，I want 任务在 Docker 容器中执行而非直接 subprocess，so that 危险命令（如 rm -rf、fork bomb）不会影响宿主机安全。
- **验收标准**:
  - Given 系统配置了 Docker
  - When 执行危险命令（如 `rm -rf /tmp/test`）
  - Then 命令应仅在 Docker 容器内执行，不影响宿主机文件系统。
  - Given Docker 服务不可用
  - When 提交任务执行
  - Then 应降级回 subprocess 模式并记录警告日志。
  - Given 容器内存超过限制（如 512MB）
  - When 执行内存密集型命令
  - Then 容器应被 OOM killer 终止，宿主机不受影响。

### 后端交付物

1. **Docker 执行器** (`src/backend/app/executor/docker_executor.py`):
   - 使用 Docker SDK 或 docker CLI 创建临时容器
   - 资源配额限制（内存 512MB、CPU 1 核、超时 60 秒）
   - 危险命令检测（可选：黑名单或 seccomp 配置）
   - 执行日志捕获（stdout/stderr）

2. **Executor 工厂/选择器** (`src/backend/app/executor/__init__.py`):
   - 根据配置选择 DockerExecutor 或 SubprocessExecutor
   - Docker 不可用时自动降级

3. **配置项** (`src/backend/config.py`):
   - `USE_DOCKER_SANDBOX` (bool, default=True)
   - `DOCKER_IMAGE` (str, default="python:3.12-slim")
   - `DOCKER_MEMORY_LIMIT` (str, default="512m")
   - `DOCKER_TIMEOUT` (int, default=60)

4. **修改现有执行逻辑** (`src/backend/app/main.py` 或 `src/backend/app/worker.py`):
   - 将现有的 subprocess 执行替换为 Executor 接口

### 前端交付物（可选）
- 配置面板显示 Docker 沙箱状态
- 配置项：启用/禁用 Docker、内存限制、超时时间

## 验收测试清单

### 后端单元测试
- [x] `test_docker_executor_runs_command` - Docker 执行器运行命令成功
- [x] `test_docker_executor_captures_output` - Docker 执行器捕获输出正确
- [x] `test_docker_executor_memory_limit` - Docker 执行器内存限制生效
- [x] `test_docker_executor_timeout` - Docker 执行器超时终止正确
- [x] `test_docker_executor_dangerous_command_isolated` - 危险命令被隔离在容器内
- [x] `test_subprocess_executor_fallback` - Subprocess 降级执行器工作正常
- [x] `test_executor_factory_selects_docker` - Executor 工厂根据配置选择正确执行器
- [x] `test_executor_factory_fallback_on_docker_unavailable` - Docker 不可用时自动降级

### 集成测试
- [x] `test_task_execution_in_docker` - 任务在 Docker 中执行（通过 execute_command 间接测试）
- [x] `test_dangerous_command_isolated` - 危险命令被隔离在容器内
- [x] `test_docker_unavailable_fallback` - Docker 不可用时降级 subprocess

### 回归测试
- [x] 不破坏现有 Sprint 1-15 的测试 - 15/15 沙箱测试通过
- [x] 任务执行流程保持不变
- [x] 控制台输出捕获正常

## 技术约束

1. **技术栈**:
   - Python Docker SDK 或直接使用 docker CLI
   - pytest + pytest-asyncio 测试

2. **安全要求**:
   - 容器必须以只读根文件系统运行（--read-only）
   - 禁止特权模式（--privileged=false）
   - 网络隔离（--network=none 或限制网络访问）

3. **YAGNI 原则**:
   - 不实现多容器编排
   - 不实现容器镜像构建
   - 不实现分布式执行

## 完成定义

- [x] 所有测试用例编写完成 (Red)
- [x] 所有测试用例通过 (Green) - 12/12 通过
- [x] Lint 检查无警告
- [x] 不破坏现有 Sprint 1-15 的测试 - 15/15 沙箱测试通过
- [x] handoff.md 更新完成
- [ ] ADR-016 决策记录创建（如有技术选型）

## 交付文件清单

- [x] `src/backend/app/sandbox.py` - Docker/Subprocess 执行器 + 工厂（修改）
- [x] `src/backend/tests/test_sandbox_docker.py` - Docker 执行器测试（新增）
