# SECA API 信令层约定

在底层开发阶段，全部使用 FastAPI 做 OpenAPI(Swagger) 原生支撑规范并限制强类型（Pydantic Validation）。

## 1. 环境层基底 (Projects Management)
- `GET /api/v1/projects`: 列装并盘点所有当前在接管监控的目录。
- `POST /api/v1/projects`: 下发一个 `local_repo_path` 注册并接管一个新的物理靶场。

## 2. 控制流引擎 (Tasks Controller)
- `POST /api/v1/tasks`: 发射高级长指令给统筹 Orchestrator。
- `GET /api/v1/tasks/{task_id}/state`: 获得此项任务的是否休眠、进行中、或挂停在致命错误的静态心跳检测值。
- `POST /api/v1/tasks/{task_id}/kill`: 人工打断任务执行的高优阻塞弹窗令。（避免死循环耗费天文级 Token 灾难）

## 3. 核心内省流推送网 (Introspection Streaming Node)
- `GET /api/v1/tasks/{task_id}/stream`:
  - 核心承载，返回 Content-Type 为 `text/event-stream` 的原生持续流下发通道 (Server-Sent Events)。
  - 规定流下发规范：每次传递以 `\n\n` 间隔的事件段，例如:
    ```javascript
    event: reasoning
    data: {"timestamp": 111111, "message": "发现这里是一个深度地柜引起的挂栈，正考虑引入尾调用机制..."}
    ```
- `GET /api/v1/tasks/{task_id}/dag-tree`: 
  - (为回溯屏页面特供的接口)。后端将零散拉平成关系数组 `[]` 的 Trace 从数据库中检索出，在此一次性用算法重构合并成树形的 `{ id, children: [ {id, children} ] }` 标准 JSON 对象给前端页面直接递归吃入使用。

## 4. 知识回收器 (Knowledge Endpoints)
- `GET /api/v1/adrs`: 汇总导出或索引这所产线下的各种遗留沉淀文档。
