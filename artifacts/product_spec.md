# SECA 产品规格说明书

## 领域词汇表
- **Harness (诊断沙箱执行层)**: 给 Agent 提供的原生隔离环境。包含控制台捕获、沙箱运行并能截留和重定位异常追踪。
- **Trace (执行路径记录)**: 单次任务中 Agent 的一切细粒度行为痕迹（含标准输入日志、决策依据、及调用时长记录）。
- **Introspection Stream (内省呈现流)**: 将 AI 推理（感知、决策、行动模型）转换为人类架构师随时可视的高亮数据流。
- **ADR (Auto-Architecture Decision Record)**: 系统结合 Trace 在非确定性技术分叉上自动写成的设计备忘录。
- **Playback (回溯图构建)**: 将数次跌宕起伏的代码修补进程结构化成包含死路与通路的因果链条树。

## 系统架构概览与流传
详见辅助设计图表：[架构指引](../docs/design/architecture.md)

## 功能(Feature) 拆解列表

### Feature 1: 动态命令执行与防溢沙箱 (Diagnostic Sandbox)
- **用户故事描述**: As a 系统核心层, I want 收容每一次 Agent 试图触发的子进程指令或代码片段运行, so that 获取到原生的 stdout 和故障异常抛出而不污染物理机。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given Agent 欲执行 `python -c "print(1/0)"`
  - When 通过沙箱网关推测执行
  - Then 应当在 3 秒内心跳返回并包裹上 `ExecutionFailed` 且捕获完整的除零报错 stderr。
- **数据流依赖草图**: `Orchestrator  --[Source Code]-->  Subprocess Sandbox  --[Intercepted Logs]-->  Trace Engine`
- **风险研判等级**：高 (Docker/进程隔离处理死锁的鲁棒性难)。**降级方案**：MVP阶段不套Docker壳，仅通过 `subprocess` 使用临时环境变量做进程包裹。

### Feature 2: 实时打字内省流 UI (Introspection Dashboard)
- **用户故事描述**: As a 人类指导者, I want 不等待漫长的长链路出最后结果，而是看着 Agent 的思维像打印机一样的流动呈现, so that 能随时确认方向是否偏航并在死锁前介入。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 系统已承载任务推演
  - When 我在主页点开仪表盘
  - Then 在不超过 500ms 延迟下，必须以折叠树的形式陆续弹播"感知"->"决策"和带语法高亮的"预演变更"记录卡片片段。
- **数据流依赖草图**: `Agent Core Logger  -->  SSE Event Manager  -->  React UI (Zustand)`
- **风险研判等级**：中 (SSE流丢失重连)。

### Feature 3: 代码推演分叉图与回溯器 (DAG Playback)
- **用户故事描述**: As a Tech Lead, I want 直观拉出这次修 Bug 中 AI 在哪条策略线上翻了车并且后来是怎么迂回的, so that 作 Code Review 兼职防呆。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 一段具有波折修改历程的结束任务
  - When 查阅该任务对应的 Playback 面板
  - Then 应呈递一张 SVG 树图，根部是原始代码，并分叉显示 `❌失败重试分支` 和带高亮的 `✅成功并合包的分支` 。
- **风险研判等级**：高 (存储链路串联)。

### Feature 4: 静默技术沉淀生成器 (Auto-ADR)
- **用户故事描述**: As a 规范守夜人, I want 代码跑通过后那些“不得不妥协做的妥协补丁”能够作为制度沉淀出来, so that 全组人不用再次踩坑。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 大循环通过并在某次红转绿中使用了冷门库解决堵塞
  - When `/qa` 放行或 `/release` 结卷时
  - Then 后台解析差异 Diff 和 Trace 推理理由，吐出合格 Markdown 加入文档库。
- **数据流依赖草图**: `Success Traces Array  -->  Anthropic API summarizer  -->  Markdown FS Writer`
- **风险研判等级**：低。

## Sprint 分解与进度

- [x] Sprint 1: 全栈基石起步 — React 纯净层 + FastAPI 健康探针 + 结构化数据库 ORM 建表连接（覆盖必要支持能力）
- [x] Sprint 2: 实现 Feature 1 — Subprocess 动态包裹沙箱实现以及 Task / Trace 的核心数据流打通存储。
- [x] Sprint 3: 实现 Feature 2 — SSE 服务器下发推送和以 Glassmorphism 为核心审美基调的前端打字机接收终端面板。
- [x] Sprint 4: 实现 Feature 3 — 引入 Mermaid/D3 在前端承揽后台组合吐出的结构树 JSON 进行图谱渲染和差分面板点选功能。
- [x] Sprint 5: 实现 Feature 4 — 结合全量回溯痕迹打造自动生成与挂载 ADR Markdown 文件的工作流节点。

## 整体项目竣工结项标准 (Definition of Done)

- [ ] 所有 Sprint (1-5) 全部接受 `/qa` 考核通过且无任何降级通过情况。
- [ ] 自动化测试全局覆盖率不低于 75%，并且 `src/tests/*` 中针对各类功能不全为 Happy path，必有脏数据校验的越界防御测试案例存在。
- [ ] 确保端到端主链路畅通：可利用一条 Prompt 自主下达修报错任务 → 界面流式观测推演 → 回放该次补丁历程 → 完结且生成了一份设计备忘录。
- [ ] 没有残存的 `P0 (系统崩溃/前端白屏)` 或 `P1 (流程致命死锁/数据写不进)` 遗留。
- [ ] `/docs` API 端点可用且全部类型安全合规响应。
