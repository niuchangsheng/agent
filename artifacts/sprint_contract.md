# Sprint 1 验收合同

## 实现范围 (Scope)
- **后端 (FastAPI)**: 初始化 Python 虚拟环境及依赖池。配置 FastAPI 启动并挂载在指定端口。建立基于 SQLModel+`aiosqlite` 的异步 SQLite 数据库引擎与空数据表挂载。实现基础 `/api/health`。
- **前端 (React/Vite)**: 借助 Vite 生成标准 SPA 页面。挂载基础的 UI 框架（无需复杂页面，只需提供状态展示点）。前端需要能正确利用配置的代理指向后端请求。
- **跨域与集成**: 确保跨越配置 (CORS) 与反向代理互通。

## TDD 测试验收标准 (Acceptance Criteria)

### 【红线约束检测】 - Evaluator 视角自我协商校验项
*(自我校验：仅测试 Happy Path 是不行的，不能假跑。所以测试集中必须要能检测：若未连通 DB 必须挂掉、如果不匹配端口则拿不到。前端要有实际 Render 检测而非仅仅运行成功)*

### 后端要求 (Backend / pytest)
- **[ ] 测试 1: 健康探针可用性**
  - 使用 `TestClient` 发送 GET `api/v1/health` 必须返回状态码 200 和包含 `{ "status": "active" }`。
  - 测试如果向未定义地址如 `/api/v1/dummy` 请求，必须得到标准化 404 包封格式。
- **[ ] 测试 2: 数据库及表元创建能力**
  - 利用 fixture 将引擎指向本地在内存 `sqlite+aiosqlite:///:memory:`，确认启动应用后数据库里生成了 `project`, `task`, `trace`, `adr` 这些表结构实体而没有崩溃报错。
  - (边界测试) 使用模拟错误强制连接无效数据库看是否能被应用 `Lifespan` 事件优雅捕获并抛异常退出而非硬崩溃。

### 前端要求 (Frontend / Vitest + React Testing Library)
- **[ ] 测试 1: 控制台页面渲染加载**
  - `App.tsx` 页面必须在没有报错的情况下完成主容器的渲染，通过捕捉元素文本 “SECA Control Panel” 是否挂载于 DOM 中可证实。
- **[ ] 测试 2: 环境代理与健康嗅探**
  - 测试前端组件被加载后发起向 `/api/v1/health` 的数据挂载状态机。模拟 API 返回正常，界面应提示 `[Connected]`，模拟离线无回应，页面应当提示超时红灯反馈。
  - *(严禁只针对 Dummy Component 作单纯的 test pass)*

## 交付完成标准
- [x] 所有 `src/tests/*` 下用例 100% 通过（已验证 `test_main.py` 与 `test_db.py` 绿灯）。
- [x] 遵守代码一致性。
- [x] TDD 日志明确。见 `artifacts/decisions/ADR-001.md` 备案决议。
