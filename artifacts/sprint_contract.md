# Sprint 3 验收合同

## 实现范围 (Scope)
- **后端 (FastAPI)**: 新增 SSE (Server-Sent Events) 下发接口 `/api/v1/tasks/{task_id}/stream`，使用 Async Generator 实时往客户端推送诊断中的 Trace 消息更新（包括 Perception, Reasoning 和 Sandbox stdout 的内容传递）。
- **前端 (React/Vite + TailwindCSS)**:
  - 引入 TailwindCSS 渲染出具有极客风格的极暗主题 + 毛玻璃（Glassmorphism）特效页面。
  - 构建 `IntrospectionDashboard` 面板。
  - 接入 `EventSource` 监听上述 SSE 接口并实现实时“打字机”追加流展示效果。

## TDD 测试验收标准 (Acceptance Criteria)

### 【红线约束检测】 - Evaluator 视角自我协商校验项
*(自我校验：SSE 推流断开重连逻辑，前端的响应式样式验证，不可使用极度简陋的纯文本列表。后端要确实能够支持长时 generator 连接。)*

### 后端要求 (Backend / pytest)
- **[ ] 测试 1: SSE 接口基础连通性**
  - 利用 `httpx.AsyncClient` 对 `/api/v1/tasks/{task_id}/stream` 发起请求，断言响应 Header 的 Content-Type 为 `text/event-stream`。
- **[ ] 测试 2: Generator 消息的流式收发**
  - 使用异步流读取接口，确保至少收到了符合 SECA `event: stream` 数据块标准格式的消息块并顺利断开。

### 前端要求 (Frontend / Vitest + RTL)
- **[ ] 测试 1: Glassmorphism 样式容断渲染**
  - 测试判断 `IntrospectionDashboard` 中是否含有了表示毛玻璃特效的 Tailwind 类名 (如 `backdrop-blur-md`, `bg-opacity-*` 或 `bg-slate-900`)。
- **[ ] 测试 2: SSE 消息的接收更新**
  - 使用 `msw` 或 `vi.mock` 模拟 EventSource 推送事件。断言主事件流组件会根据推送更新 DOM，新增一条 "察觉到代码异味" 文字。

## 交付完成标准
- [x] 后端测试通过 `tests/test_stream.py`。
- [x] 前端测试通过 `tests/Dashboard.test.tsx`。
- [x] 前端引入 `tailwindcss` 并搭建完成了真正的 Hacker-style 暗黑面板 MVP 体。（引入 ADR-003）
