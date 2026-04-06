# 上下文交接文档 (Handoff.md)

## 最新进度与心跳留存
- **最近更新时间**: 2026-04-07
- **更新方身份**: `/run` 宏控制器 (驱动了 Generator 和 Evaluator)

## 当前游标与系统状态
- **核心阶段落点**: **Sprint 2 (Subprocess 动态诊断沙箱引擎)** 已彻底通关结项。
- **目标执行体进展**:
  - `src/backend/app/sandbox.py` 借由 `asyncio.create_subprocess_shell` 完善了安全的底层接管逻辑，处理了异常 `stderr` 及 `is_timeout` 等安全脱产状态标识。
  - 完成了 `/api/v1/projects` 和 `/api/v1/tasks` 两个控制流路由，可正常往 SQLite 通过异步 ORM 落盘数据。
  - Generator 的新模块测试案例 `test_sandbox.py` 和 `test_tasks.py` 100%覆盖并通过，写入了架构决策（ADR-002：Subprocess的沙盒方案替代方案）。
  - Evaluator 下发 `[x]` 令牌，Sprint 2 宣告完成。

## 关键架构与约定回顾
- **最近的关键决策落子**: [ADR-002] 使用 Subprocess 隔离替代 Docker 沙箱执行，保障推演阶段的速度流转避免僵尸进程。
- **待攻克的难题/未完成清单**: 下一战：**Sprint 3** (实施将流媒体数据通过 SSE `Server-Sent Events` 传输到前端以呈现真正的酷炫的内省控制面板)。

## 下游行动建议 (Action Requested)
- **对于 AI**: 等待唤醒。
- **对于人类**: 第二段“硬骨头”（诊断外壳和进程隔离）已被完美斩落。如果希望继续看到基于这套内核输出前端呈现面板的功能流片（Sprint 3），请继续输入 **“ `/run` ”** 推动流水线狂飙！
