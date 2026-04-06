# Sprint 2 验收合同

## 实现范围 (Scope)
- **Harness Sandbox (Subprocess 引擎)**: 建立一个纯 Python 实现的执行沙箱模块。能够通过给定命令（比如 `python -c "print(1/0)"`），并在子进程中执行。设置超时机制，强制捕获 `stdout`，`stderr`，和退出码 `exit_code`，包裹成标准的 `ExecutionResult` 对象返回。
- **任务/痕迹 API (Task & Trace Data Flow)**: 在 FastAPI 中实现 `/api/v1/tasks` 路由发起长期探知任务，记录到 Task 表中；为每次子进程调用的结果建立 Trace 关联保存到 SQLite。

## TDD 测试验收标准 (Acceptance Criteria)

### 【红线约束检测】 - Evaluator 视角自我协商校验项
*(自我校验要求：绝对不允许伪造假实现，必须使用真实的异常代码验证 sandbox 的容错和防御能力，必须验证数据库实体真正被创建。)*

### 后端要求 (Backend / pytest)
- **[ ] 测试 1: Sandbox 正常退出流的截获**
  - 使用 Sandbox 模块执行简单的命令：`echo "SECA Test"`。
  - 断言 `stdout` 包含 "SECA Test"。断言 `exit_code` 是 0，且不抛出未捕捉异常。
- **[ ] 测试 2: Sandbox 致命报错的防溢及捕获**
  - 使用 Sandbox 执行注定会失败的命令：`python3 -c "1/0"`。
  - 测试断言必须安全返回，`exit_code` 非0，同时 `stderr` 必须包含 `ZeroDivisionError`，宿主系统绝对不可崩溃。
- **[ ] 测试 3: 超时机制防挂死**
  - 利用 `sleep 5` 执行，沙箱限时设置为 `1` 秒。必须能主动掐断该进程，并返回状态标记超时 (Timeout)。
- **[ ] 测试 4: Task / Trace 落盘与数据库强关联**
  - 创建一个模拟任务 API 并调用后，能断言 SQLAlchemy 查询到最新的 Task 及该起任务产生的首个 Trace。

## 交付完成标准
- [x] 所有测试用例 `tests/test_sandbox.py`, `tests/test_tasks.py` 必须能在隔离环境中跑通全绿。
- [x] `subprocess` 运用得当，严格使用了 `asyncio.create_subprocess_shell` 等非阻塞机制。
- [x] 测试用例需在实际功能撰写前入库以保证无作弊行为。（已生成 ADR-002）
