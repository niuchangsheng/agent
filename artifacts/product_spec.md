# SECA 产品规格说明书 (Product Spec)

## 领域词汇表 (Glossary)
- **Harness (诊断外壳)**: 面向 Agent 的动态执行外壳，包含沙箱和跟踪反馈回路。用于收容 Agent 的执行，提供即时边界和保护。
- **Trace (执行轨迹)**: Agent 执行期间的单步记录，包括 stdout/stderr、执行耗时、系统调用记录等。
- **Introspection Stream (内省流)**: 从 Agent 的感知(Perception)、逻辑推理(Reasoning)到预演(Preview)的实时流式输出，面向人类架构师进行系统透明化展示。
- **ADR (Architecture Decision Record)**: 自动生成的架构决策记录。
- **RCA (Root Cause Analysis)**: 针对 Trace 失败情况自动执行的根因推导过程。

## 系统架构概览
详见 [系统架构设计](../docs/design/architecture.md)

## Feature 列表

### Feature 1: 动态诊断执行沙箱 (Dynamic Diagnostic Harness)
- **用户故事**: As a 技术架构师, I want 一个安全的隔离沙箱环境来运行 Agent, so that 避免恶意或错误代码破坏宿主机，并能实时捕获所有执行细节。
- **验收标准**:
  - Given 生成了一段包含控制台输出和系统异常的代码, When 注入沙箱执行, Then 代码应在限定时间的容器环境内运行并能够截获完整的 stdout, stderr 和退出码。
  - Given 发生并发死锁等代码级异常, When 捕获后, Then Harness 能自动注入错误栈并引导二次修复。
- **复杂度**: 困难 (MVP 阶段沙箱可通过 `subprocess` 子进程级隔离替代 Docker)
- **MVP 必要性**: 必须
- **风险等级**: 高

### Feature 2: 实时 Trace 捕获与内省流展示 (Introspection Stream)
- **用户故事**: As a Tech Lead, I want 实时看到 Agent 的思考和试错全过程, so that 建立对 AI 产出代码的白盒信任，而不是等待一个最终黑盒结果。
- **验收标准**:
  - Given 引擎正在后台执行复杂逻辑推演, When 我打开前台控制面板, Then 可以在界面上流式看到它的感知分析、Trade-off 对比以及即将发生的文件变更 DIFF 预演。
- **复杂度**: 中等
- **MVP 必要性**: 必须

### Feature 3: 任务回放与诊断可视化 (Post-mortem Playback)
- **用户故事**: As a 新进工程师, I want 像播放录像一样回退查看某行代码是通过怎样的失败分叉逻辑最终跑通的, so that 快速学习之前的架构上下文。
- **验收标准**:
  - Given 完结的旧任务, When 我进入回放模式并点击特定的源代码边界, Then 系统能展示一个逻辑分叉树（Node Tree），高亮最后成功的路径及之前失败的诊断记录分支。
- **复杂度**: 困难
- **MVP 必要性**: 重要

### Feature 4: 自动架构决策记录 (Auto-ADR 生成)
- **用户故事**: As a 团队规范维护者, I want 系统能自动沉淀并落盘 Agent 在过程中产生的技术选型决策, so that 团队知识得以传承，并维持架构一致性。
- **验收标准**:
  - Given 发生如引入新状态库、切换数据库等核心决策, When Sprint或任务结束, Then 在仓库的指定目录下将自动生成 Markdown 格式的完整 ADR 文件。
- **复杂度**: 中等
- **MVP 必要性**: 必须

### Feature 5: 意图探测与遗留系统重构 (Legacy Archaeology)
- **用户故事**: As a 架构师, I want 系统能反向解析未注视旧代码的约束和序列图, so that 我能安全地开始对其执行大规模重构。
- **复杂度**: 困难
- **MVP 必要性**: 可延后

## Sprint 分解

- [ ] Sprint 1: 核心数据模型建立，配置全栈项目脚手架 (React + FastAPI) 联通健康检查
- [ ] Sprint 2: 动态诊断基础引擎 (Subprocess沙箱) 与 Task/Trace 持久化链路
- [ ] Sprint 3: Server-Sent Events (SSE) 服务构建与前端内省流展示 UI
- [ ] Sprint 4: 逻辑分叉数据回溯器后台接口与前端 D3/Mermaid 路径树渲染
- [ ] Sprint 5: 上下文捕获型机制接入，Auto-ADR 解析引擎与文件生成
- [ ] Sprint 6: 联调，支持通过 Prompt 发起一个简单的修复任务，走通沙箱跟踪并可视化展示端到端流程

## 项目验收标准
- [ ] 所有 Sprint QA 通过 (全部标记为 `[x]`)
- [ ] 全量测试覆盖率 ≥ 70%
- [ ] 端到端用户流程可走通：发起新架构修复 → 沙箱执行 → 网页呈现内省流 → 重放逻辑树 → 生成 ADR
- [ ] API 文档可正常访问
- [ ] 零容忍：无 P0/P1 级别已知崩溃Bug
