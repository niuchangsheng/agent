# SECA 产品规格说明书

## 版本历史
| 版本 | 状态 | 周期 | 摘要 |
|------|------|------|------|
| v1.0 | ✅ 已完成 | 2026-04-01 ~ 2026-04-07 | MVP: 核心沙箱 + 内省流 + DAG 回放 + ADR 生成 |
| v1.1 | ✅ 已完成 | 2026-04-12 ~ 2026-04-12 | 增强版：配置管理 + 任务队列 + 基础认证 |
| v1.2 | 🔄 规划中 | 2026-04-13 ~ ? | 持久化 + 安全加固 + 可观测性 |

## 领域词汇表
- **Harness (诊断沙箱执行层)**: 给 Agent 提供的原生隔离环境。包含控制台捕获、沙箱运行并能截留和重定位异常追踪。
- **Trace (执行路径记录)**: 单次任务中 Agent 的一切细粒度行为痕迹（含标准输入日志、决策依据、及调用时长记录）。
- **Introspection Stream (内省呈现流)**: 将 AI 推理（感知、决策、行动模型）转换为人类架构师随时可视的高亮数据流。
- **ADR (Auto-Architecture Decision Record)**: 系统结合 Trace 在非确定性技术分叉上自动写成的设计备忘录。
- **Playback (回溯图构建)**: 将数次跌宕起伏的代码修补进程结构化成包含死路与通路的因果链条树。
- **Project Context (项目上下文)**: 一个独立的诊断靶场，拥有自己的环境变量、沙箱配额和 Trace 日志隔离。
- **Task Queue (任务队列)**: 异步执行容器，支持长时任务排队、进度轮询和并发控制。
- **Redis Queue (持久化队列)**: 基于 Redis 的任务持久化存储，支持进程重启后任务不丢失。
- **Audit Trail (审计追踪)**: 完整的操作日志链，支持追溯谁在什么时候做了什么操作。

## 系统架构概览与流传
详见辅助设计图表：[架构指引](../docs/design/architecture.md)

## 功能 (Feature) 拆解列表

### Feature 8: Redis 任务队列持久化 (Redis Queue Persistence)
- **用户故事描述**: As a 系统运维者，I want 任务队列在进程重启后不丢失正在排队或执行的任务，so that 长时任务不会因服务重启而白跑。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 任务队列中有 3 个待执行任务，其中一个正在执行
  - When 后端服务意外重启
  - Then 重启后应自动恢复未完成任务，已执行任务保留进度记录。
  - Given Redis 服务不可用
  - When 提交新任务
  - Then 应降级回内存队列模式并记录警告日志。
- **数据流依赖草图**: `Task Submission --> Redis Queue --> Worker Pool --> Status Persistence`
- **风险研判等级**：高 (Redis 连接稳定性、任务状态一致性)。**降级方案**：Redis 不可用时自动降级回内存队列。

### Feature 9: API Key 加密存储 (Secure Key Storage)
- **用户故事描述**: As a 安全合规官，I want API Key 在数据库中以加密形式存储而非明文，so that 即使数据库泄露也不会暴露敏感凭证。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 用户创建新的 API Key
  - When 保存到数据库时
  - Then 密钥应当使用 AES-256 加密存储，仅创建时向用户展示一次明文。
  - Given 用户提交 API Key 进行认证
  - When 中间件验证时
  - Then 应当安全比对加密后的哈希值而非解密存储。
  - Given API Key 有过期时间
  - When 超过过期时间
  - Then 自动拒绝该 Key 的所有请求并返回 401。
- **数据流依赖草图**: `API Key Creation --> Cryptographic Hash --> Encrypted Storage --> Hash Compare on Auth`
- **风险研判等级**：中 (密钥管理、加密算法选择)。**降级方案**：使用成熟的 cryptography 库，不造轮子。

### Feature 10: 审计日志增强 (Audit Trail Enhancement)
- **用户故事描述**: As a 合规审计员，I want 审计日志记录完整的操作上下文（IP 地址、User-Agent、操作耗时），so that 满足安全合规要求并支持问题追溯。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 用户执行写操作（创建/更新/删除）
  - When 操作完成后
  - Then 审计日志应记录：操作者 API Key ID、IP 地址、User-Agent、操作类型、目标资源、操作耗时。
  - Given 审计员需要查询历史操作
  - When 访问审计日志端点
  - Then 应支持按时间范围、操作类型、操作者筛选并分页返回。
- **数据流依赖草图**: `Request --> Middleware --> Audit Logger --> Database`
- **风险研判等级**：低。**降级方案**：N/A。

### Feature 11: 任务进度 ETA 预测 (ETA Prediction)
- **用户故事描述**: As a 任务提交者，I want 看到长时任务的预计完成时间 (ETA)，so that 合理安排等待时间并在完成后返回。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 一个长时任务已执行 50% 进度，耗时 30 秒
  - When 用户查看任务详情
  - Then 应显示预计剩余时间和预计完成时间点（如 "预计 2026-04-13 15:30 完成，剩余约 30 秒"）。
  - Given 任务进度更新
  - When ETA 计算时
  - Then 应使用移动平均算法平滑瞬时波动，避免 ETA 大幅跳变。
- **数据流依赖草图**: `Task Progress Updates --> Moving Average Calculator --> ETA Estimator --> UI Display`
- **风险研判等级**：中 (ETA 准确性、进度非线性场景)。**降级方案**：进度更新少于 3 次时不显示 ETA，仅显示"计算中..."。

### Feature 12: 系统监控仪表盘 (System Monitoring Dashboard)
- **用户故事描述**: As a 运维工程师，I want 实时查看系统健康指标（CPU、内存、队列长度、响应延迟），so that 及时发现并处理性能瓶颈。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 系统已运行 1 小时
  - When 运维打开监控仪表盘
  - Then 应显示：当前并发任务数、队列等待数、平均响应延迟 (P50/P95)、内存使用量、Redis 连接状态。
  - Given 某项指标超过阈值（如队列长度 > 100）
  - When 监控轮询时
  - Then 应以视觉警告（橙色/红色）高亮异常指标。
- **数据流依赖草图**: `Metrics Collector --> Time-series Aggregator --> SSE Stream --> Dashboard`
- **风险研判等级**：中 (指标采集性能开销)。**降级方案**：指标采集频率限流至 10 秒/次，避免影响主业务。

### Feature 13: 任务优先级与插队 (Task Priority & Preemption)
- **用户故事描述**: As a 团队管理者，I want 为紧急任务设置高优先级使其插队执行，so that 关键任务可以绕过队列等待立即处理。
- **面向最终效果的验收标准 (Given/When/Then)**:
  - Given 队列中有 5 个普通优先级任务等待
  - When 提交一个高优先级任务
  - Then 高优先级任务应立即插入队首，下一个空闲 Worker 优先执行它。
  - Given 两个相同优先级的任务
  - When 队列调度时
  - Then 应遵循 FIFO 原则，先提交的先执行。
- **数据流依赖草图**: `Priority Task Submission --> Sorted Queue (Priority ASC, CreatedAt ASC) --> Worker`
- **风险研判等级**：中 (优先级饥饿问题)。**降级方案**：限制高优先级任务比例不超过 20%，避免普通任务永远无法执行。

## Sprint 分解与进度

### v1.0 (已完成)
- [x] Sprint 1: 全栈基石起步 — React 纯净层 + FastAPI 健康探针 + 结构化数据库 ORM 建表连接（覆盖必要支持能力）
- [x] Sprint 2: 实现 Feature 1 — Subprocess 动态包裹沙箱实现以及 Task / Trace 的核心数据流打通存储。
- [x] Sprint 3: 实现 Feature 2 — SSE 服务器下发推送和以 Glassmorphism 为核心审美基调的前端打字机接收终端面板。
- [x] Sprint 4: 实现 Feature 3 — 引入 Mermaid/D3 在前端承揽后台组合吐出的结构树 JSON 进行图谱渲染和差分面板点选功能。
- [x] Sprint 5: 实现 Feature 4 — 结合全量回溯痕迹打造自动生成与挂载 ADR Markdown 文件的工作流节点。

### v1.1 (已完成)
- [x] Sprint 6: 配置管理中心 — 实现 Feature 5 ✅ QA 通过 (9.075/10)
- [x] Sprint 7: 异步任务队列 — 实现 Feature 6 ✅ QA 通过 (9.075/10)
- [x] Sprint 8: 基础认证与权限 — 实现 Feature 7 ✅ QA 通过 (9.175/10)

### v1.2 (进行中)
- [x] Sprint 9: Redis 队列持久化 — 实现 Feature 8 ✅ QA 通过 (8.80/10)
  - 后端：Redis 连接池、任务状态持久化、崩溃恢复逻辑
  - 验收：服务重启后未完成任务自动恢复、Redis 不可用时降级内存队列
  
- [x] Sprint 10: API Key 加密存储 — 实现 Feature 9 ✅ QA 通过 (8.80/10)
  - 后端：bcrypt 库集成、密钥哈希比对、过期时间验证
  - 验收：数据库中存储加密哈希、明文仅展示一次、过期 Key 自动失效
  
- [x] Sprint 11: 审计日志增强 — 实现 Feature 10 ✅ QA 通过 (8.80/10)
  - 后端：AuditLog 模型扩展（IP、User-Agent、耗时）、审计查询 API
  - 前端：审计日志查询面板、筛选器（待后续实现）
  - 验收：写操作完整记录、支持时间范围/操作类型筛选
  
- [x] Sprint 12: 任务 ETA 预测 — 实现 Feature 11 + Feature 13 (优先级) ✅ QA 通过 (8.80/10)
  - 后端：ETA 计算器（移动平均）、任务优先级字段、排序队列
  - 前端：ETA 显示组件、优先级选择器（待后续实现）
  - 验收：ETA 平滑更新、高优先级插队正确
  
- [/] Sprint 13: 系统监控仪表盘 — 实现 Feature 12
  - 后端：指标采集器、监控 SSE 端点
  - 前端：监控仪表盘 UI、阈值告警视觉
  - 验收：实时显示并发数/延迟/内存、异常指标高亮

## 整体项目竣工结项标准 (Definition of Done)

### v1.0 DoD (✅ 已完成)
- [x] 所有 Sprint (1-5) 全部接受 `/qa` 考核通过且无任何降级通过情况。
- [x] 自动化测试全局覆盖率不低于 75%，并且 `src/tests/*` 中针对各类功能不全为 Happy path，必有脏数据校验的越界防御测试案例存在。
- [x] 确保端到端主链路畅通：可利用一条 Prompt 自主下达修报错任务 → 界面流式观测推演 → 回放该次补丁历程 → 完结且生成了一份设计备忘录。
- [x] 没有残存的 `P0 (系统崩溃/前端白屏)` 或 `P1 (流程致命死锁/数据写不进)` 遗留。
- [x] `/docs` API 端点可用且全部类型安全合规响应。

### v1.1 DoD (✅ 已完成)
- [x] Sprint 6-8 全部 `/qa` 通过
- [x] 支持至少 3 个并发任务同时执行
- [x] 任务平均响应延迟 < 100ms (P95)
- [x] 所有 API 端点具备认证保护
- [x] 配置管理面板支持实时修改并热加载
- [x] 审计日志可追溯所有写操作

### v1.2 DoD (待完成)
- [ ] Sprint 9-13 全部 `/qa` 通过
- [ ] Redis 队列支持任务持久化，重启不丢失
- [ ] API Key 加密存储，数据库无明文
- [ ] 审计日志包含 IP、User-Agent、操作耗时
- [ ] 长时任务 ETA 预测误差 < 20%
- [ ] 监控仪表盘 10 秒内刷新指标
- [ ] 高优先级任务可正确插队

## 技术债务与风险追踪

| 风险项 | 等级 | 当前缓解措施 | 长期解决方案 | 状态 |
|--------|------|--------------|--------------|------|
| 沙箱非 Docker 隔离 | 高 | 临时环境变量包裹 | v2.0 引入轻量级容器 | 待解决 |
| 内存队列非持久化 | 中 | 进程保活监控 | v1.2 Sprint 9 Redis 迁移 | ✅ 规划中 |
| API Key 明文存储 | 中 | 文件权限限制 | v1.2 Sprint 10 加密存储 | ✅ 规划中 |
| 审计日志缺 IP 记录 | 低 | 基础操作记录 | v1.2 Sprint 11 增强 | ✅ 规划中 |
| 缺 ETA 预测 | 低 | 显示进度百分比 | v1.2 Sprint 12 | ✅ 规划中 |
| 缺系统监控 | 中 | 日志查看 | v1.2 Sprint 13 仪表盘 | ✅ 规划中 |
