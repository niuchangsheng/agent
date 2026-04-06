# Agent 间状态通信仓库

本 `artifacts/` 目录不包含任何业务产品源代码逻辑。
它被用作 Antigravity Agent 底层三角色（Planner / Generator / Evaluator）进行流转协作时保存跨会话上下文生命周期与握手约定的存放处。不应当将此文件纳入到业务代码打包范畴。

## 文件索引与定位

- `product_spec.md`: 由 Planner 初始化输出的核心蓝本，管理拆解 Sprint 状态（状态流转器 `[ ]`, `[/]`, `[x]`, `[!]`）。
- `sprint_contract.md`: 由 Generator 根据下一级 Sprint 起草和自我校验并锁定功能界限后的具体测试验收约定，也是引发功能代码重构的起始锚点。
- `qa_feedback.md`: 由 Evaluator 测试验收给出的结果输出单表与分数裁定矩阵。
- `handoff.md`: 处于各工作流首/尾位自动进行读取/写入的心跳级进度记录纸，防止 Token Context 失落切断导致失忆，包含着当前的系统游标。
- `decisions/`: ADR 架构技术折中方案下落的地方。
