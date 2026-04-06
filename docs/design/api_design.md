# SECA API 接口设计

全部基于 RESTful 规范定义后端路由集合，由 FastAPI （遵循 OpenAPI）提供支持。

## 1. 项目与环境管理 (Project API)
- `GET /api/v1/projects`
  - 功能：获取当前接管的全部项目清单
  - 响应：`Array<Project>`
- `POST /api/v1/projects`
  - 功能：初始化新工作区设定环境
  - 负载：`{ "name": string, "repo_path": string }`
- `GET /api/v1/projects/{project_id}/health`
  - 功能：针对该工程检测沙箱支持环境（如 Python版本、NPM准备就绪状态）

## 2. 任务流控调度 (Task Control API)
- `GET /api/v1/tasks?project_id={id}`
  - 功能：查询任务历史列表页
- `POST /api/v1/tasks`
  - 功能：下发生成/重构/分析等高级命令
  - 负载：`{ "objective": "修复用户登录验证的内存泄漏" }`
- `POST /api/v1/tasks/{task_id}/pause`
  - 功能：当消耗异常 Token 或者诊断陷入死循环时强制打断阻断。

## 3. 核心内省流 (Introspection Stream API)
- `GET /api/v1/tasks/{task_id}/stream`
  - **重要度**：极高
  - 功能：使用 `Server-Sent Events (SSE)` (Content-Type: text/event-stream) 提供毫秒级实时 Agent 推流。
  - Payload Packet 示例：`{"type": "REASONING", "log": "Considering alternative logic flow...", "timestamp": "2026-T12..."}`
- `GET /api/v1/tasks/{task_id}/tree`
  - 功能：一次性提取完整逻辑分叉 Trace 图谱 (用于 Dashboard 回溯)。
  - 返回完整具备 parent_id 的平级数组以渲染 DAG 树。

## 4. 知识/资产 (Assets API)
- `GET /api/v1/adrs?project_id={id}`
  - 功能：检出生成的全部 ADR 文档内容。
  - 响应：富文本 Markdown Object 对象集。
- `GET /api/v1/metrics/roi`
  - 功能：资本效率统计数据暴露端点，返回消耗 Token 与修复 Bug 数量的比值。
