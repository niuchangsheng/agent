# SECA 产品规格说明书

## 版本历史
| 版本 | 状态 | 周期 | 摘要 |
|------|------|------|------|
| v1.0 | ✅ 已完成 | 2026-04-01 ~ 2026-04-07 | MVP: 核心沙箱 + 内省流 + DAG 回放 + ADR 生成 |
| v1.1 | 🔄 规划中 | 2026-04-12 ~ ? | 增强版：配置管理 + 任务队列 + 基础认证 |

## 领域词汇表
- **Harness (诊断沙箱执行层)**: 给 Agent 提供的原生隔离环境。包含控制台捕获、沙箱运行并能截留和重定位异常追踪。
- **Trace (执行路径记录)**: 单次任务中 Agent 的一切细粒度行为痕迹（含标准输入日志、决策依据、及调用时长记录）。
- **Introspection Stream (内省呈现流)**: 将 AI 推理（感知、决策、行动模型）转换为人类架构师随时可视的高亮数据流。
- **ADR (Auto-Architecture Decision Record)**: 系统结合 Trace 在非确定性技术分叉上自动写成的设计备忘录。
- **Playback (回溯图构建)**: 将数次跌宕起伏的代码修补进程结构化成包含死路与通路的因果链条树。
- **Project Context (项目上下文)**: 一个独立的诊断靶场，拥有自己的环境变量、沙箱配额和 Trace 日志隔离。
- **Task Queue (任务队列)**: 异步执行容器，支持长时任务排队、进度轮询和并发控制。

## 系统架构概览与流传
详见辅助设计图表：[架构指引](../docs/design/architecture.md)

## 功能 (Feature) 拆解列表

### Feature 1: 动态命令执行与防溢沙箱 (Diagnostic Sandbox)
- **用户故事描述**: As a 系统核心层，I want 收容每一次 Agent 试图触发的子进程指令或代码片段运行，so that 获取到原生的 stdout 和故障异常抛出而不污染物理机。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given Agent 欲执行 `python -c "print(1/0)"`
  - When 通过沙箱网关推测执行
  - Then 应当在 3 秒内心跳返回并包裹上 `ExecutionFailed` 且捕获完整的除零报错 stderr。
- **数据流依赖草图**: `Orchestrator --[Source Code]--> Subprocess Sandbox --[Intercepted Logs]--> Trace Engine`
- **风险研判等级**：高 (Docker/进程隔离处理死锁的鲁棒性难)。**降级方案**：MVP 阶段不套 Docker 壳，仅通过 `subprocess` 使用临时环境变量做进程包裹。

### Feature 2: 实时打字内省流 UI (Introspection Dashboard)
- **用户故事描述**: As a 人类指导者，I want 不等待漫长的长链路出最后结果，而是看着 Agent 的思维像打印机一样的流动呈现，so that 能随时确认方向是否偏航并在死锁前介入。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 系统已承载任务推演
  - When 我在主页点开仪表盘
  - Then 在不超过 500ms 延迟下，必须以折叠树的形式陆续弹播"感知"->"决策"和带语法高亮的"预演变更"记录卡片片段。
- **数据流依赖草图**: `Agent Core Logger --> SSE Event Manager --> React UI (Zustand)`
- **风险研判等级**：中 (SSE 流丢失重连)。

### Feature 3: 代码推演分叉图与回溯器 (DAG Playback)
- **用户故事描述**: As a Tech Lead, I want 直观拉出这次修 Bug 中 AI 在哪条策略线上翻了车并且后来是怎么迂回的，so that 作 Code Review 兼职防呆。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 一段具有波折修改历程的结束任务
  - When 查阅该任务对应的 Playback 面板
  - Then 应呈递一张 SVG 树图，根部是原始代码，并分叉显示 `❌失败重试分支` 和带高亮的 `✅成功并合包的分支`。
- **风险研判等级**：高 (存储链路串联)。

### Feature 4: 静默技术沉淀生成器 (Auto-ADR)
- **用户故事描述**: As a 规范守夜人，I want 代码跑通过后那些"不得不妥协做的妥协补丁"能够作为制度沉淀出来，so that 全组人不用再次踩坑。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 大循环通过并在某次红转绿中使用了冷门库解决堵塞
  - When `/qa` 放行或 `/release` 结卷时
  - Then 后台解析差异 Diff 和 Trace 推理理由，吐出合格 Markdown 加入文档库。
- **数据流依赖草图**: `Success Traces Array --> Anthropic API summarizer --> Markdown FS Writer`
- **风险研判等级**：低。

### Feature 5: 多项目配置管理中心 (Configuration Hub) [v1.1 新增]
- **用户故事描述**: As a Tech Lead 同时管理多个诊断靶场，I want 为每个 Project 配置独立的环境变量、沙箱资源配额和持久化存储路径，so that 并行执行多个 Agent 任务时不会互相污染且资源可控。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 系统已注册 Project A 和 Project B
  - When Project A 设置 `SANDBOX_TIMEOUT=30s` 和 `MAX_MEMORY=512MB`，Project B 设置不同值
  - Then 两个项目的任务执行时应当各自遵循独立的配额限制，互不干扰。
  - Given 用户在 Dashboard 配置面板修改某个 Project 的环境变量
  - When 保存配置后发起新任务
  - Then 新任务应当在 500ms 内加载最新配置并生效。
- **数据流依赖草图**: `Dashboard Config Form --> POST /api/v1/projects/{id}/config --> Config Store --> Sandbox Executor`
- **风险研判等级**：中 (配置热加载的竞态条件)。**降级方案**：配置修改后仅对新任务生效，不中断运行中任务。

### Feature 6: 异步任务队列 (Async Task Queue) [v1.1 新增]
- **用户故事描述**: As a 系统用户，I want 提交长时任务（如全量代码重构）后无需保持 SSE 连接等待，so that 可以离线并在完成后接收通知。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 任务队列中有 3 个待执行任务
  - When 并发限制为 2 个并发槽位
  - Then 前两个任务应当并行执行，第三个任务在队列中等待，并在任一任务完成后自动开始。
  - Given 一个长时任务正在执行
  - When 用户刷新 Dashboard
  - Then 应当显示任务进度百分比和预计剩余时间。
- **数据流依赖草图**: `Task Submission --> Redis Queue --> Worker Pool --> Status Polling API`
- **风险研判等级**：高 (队列状态一致性、Worker 崩溃恢复)。**降级方案**：MVP 使用内存队列 + 定时轮询，生产环境迁移至 Redis/RQ。

### Feature 7: 基础认证与权限 (Auth & Access Control) [v1.1 新增]
- **用户故事描述**: As a 团队管理者，I want 限制只有持有有效 API Key 的用户才能提交任务或查看敏感 Trace，so that 防止未授权访问和操作审计。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 一个未携带 `X-API-Key` 头部的请求
  - When 尝试访问 `POST /api/v1/tasks`
  - Then 应当返回 `401 Unauthorized` 且不带敏感信息。
  - Given 一个只读权限的 API Key
  - When 尝试访问 `DELETE /api/v1/tasks/{id}`
  - Then 应当返回 `403 Forbidden`。
  - Given 所有写操作
  - When 操作完成后
  - Then 应当在审计日志中记录 `who did what at when`。
- **数据流依赖草图**: `Request --> API Key Middleware --> Permission Check --> Audit Logger --> Handler`
- **风险研判等级**：中 (密钥存储安全、权限模型复杂度)。**降级方案**：MVP 仅支持单层级 API Key 认证，暂不实现 RBAC 角色系统。

## Sprint 分解与进度

### v1.0 (已完成)
- [x] Sprint 1: 全栈基石起步 — React 纯净层 + FastAPI 健康探针 + 结构化数据库 ORM 建表连接（覆盖必要支持能力）
- [x] Sprint 2: 实现 Feature 1 — Subprocess 动态包裹沙箱实现以及 Task / Trace 的核心数据流打通存储。
- [x] Sprint 3: 实现 Feature 2 — SSE 服务器下发推送和以 Glassmorphism 为核心审美基调的前端打字机接收终端面板。
- [x] Sprint 4: 实现 Feature 3 — 引入 Mermaid/D3 在前端承揽后台组合吐出的结构树 JSON 进行图谱渲染和差分面板点选功能。
- [x] Sprint 5: 实现 Feature 4 — 结合全量回溯痕迹打造自动生成与挂载 ADR Markdown 文件的工作流节点。

### v1.1 (进行中)
- [x] Sprint 6: 配置管理中心 — 实现 Feature 5 ✅ QA 通过 (9.075/10)
  - 后端：`ProjectConfig` 模型、`GET/PUT/POST /api/v1/projects/{id}/config` 端点
  - 前端：配置管理面板 UI、环境变量编辑器、沙箱配额滑块控件
  - 验收：3 个并发任务各自遵循独立配额、配置修改后新任务立即生效

- [x] Sprint 7: 异步任务队列 — 实现 Feature 6 ✅ QA 通过 (9.075/10)
  - 后端：TaskQueue 内存队列、Worker 池管理、7 个队列 API 端点
  - 前端：任务队列 Dashboard、进度条组件、实时轮询
  - 验收：2 并发限制下任务正确调度、长时任务进度可视化

- [ ] Sprint 8: 基础认证与权限 — 实现 Feature 7
  - 后端：API Key 中间件、权限装饰器、审计日志表 `AuditLog`
  - 前端：API Key 管理面板、登录态持久化、401/403 错误处理
  - 验收：无 Key 请求被拦截、写操作审计可查

## 整体项目竣工结项标准 (Definition of Done)

### v1.0 DoD (✅ 已完成)
- [x] 所有 Sprint (1-5) 全部接受 `/qa` 考核通过且无任何降级通过情况。
- [x] 自动化测试全局覆盖率不低于 75%，并且 `src/tests/*` 中针对各类功能不全为 Happy path，必有脏数据校验的越界防御测试案例存在。
- [x] 确保端到端主链路畅通：可利用一条 Prompt 自主下达修报错任务 → 界面流式观测推演 → 回放该次补丁历程 → 完结且生成了一份设计备忘录。
- [x] 没有残存的 `P0 (系统崩溃/前端白屏)` 或 `P1 (流程致命死锁/数据写不进)` 遗留。
- [x] `/docs` API 端点可用且全部类型安全合规响应。

### v1.1 DoD (待完成)
- [ ] Sprint 6-8 全部 `/qa` 通过
- [ ] 支持至少 3 个并发任务同时执行
- [ ] 任务平均响应延迟 < 100ms (P95)
- [ ] 所有 API 端点具备认证保护
- [ ] 配置管理面板支持实时修改并热加载
- [ ] 审计日志可追溯所有写操作

## 技术债务与风险追踪

| 风险项 | 等级 | 当前缓解措施 | 长期解决方案 |
|--------|------|--------------|--------------|
| 沙箱非 Docker 隔离 | 高 | 临时环境变量包裹 | v2.0 引入轻量级容器 |
| 内存队列非持久化 | 中 | 进程保活监控 | Sprint 7 后迁移 Redis |
| API Key 明文存储 | 中 | 文件权限限制 | v1.2 引入密钥加密 |
