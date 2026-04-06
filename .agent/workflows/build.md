---
description: 执行 Generator 角色，负责 TDD 技术开发与 Sprint 合同签署
---

1. 读取 `skills/generator/SKILL.md` 获取 TDD 全栈工程师的角色规范。
2. 尝试读取 `artifacts/handoff.md` 恢复此前的技术对话上下文与卡点障碍。
3. 读取 `artifacts/product_spec.md` 确认整体进度状态。
4. 若存在 `artifacts/qa_feedback.md`，先读取并优先处理 QA 指定的必修打回要求 `[!]`。
5. 选取下一个尚未开始 `[ ]` 或被 QA 打回重提 `[!]` 的 Sprint，更新 `product_spec.md` 里面该 Sprint 列表的 Checkbox 标记为 `[/]` 正在运行。
6. 起草基于该块功能的具体交付要求，将这阶段的内容作为“验收合同”，撰写输出到 `artifacts/sprint_contract.md`。
7. 【自我协商验证】
   - 以 Evaluator 视角交叉验证自己写的 `sprint_contract.md`。
   - 它是否过于宽松？能否容易推导出反向边界测试（Red 路经）？
   - 根据查遗补漏后的标准，覆盖更新最终版合同书。的
8. 【执行 TDD 环 (RGR)】
   - 🔴 **Red (测试先行)**：根据敲定的合同，编写包含针对性（不要只写Happy Path）的测试文件存入 `src/tests/`，确认目前的测试态必然是红通通的失败状态。
   - 🟢 **Green (最少实现)**：编写恰好能使这些失败用例转绿的核心逻辑到 `src/`。严禁“YAGNI - You Aren't Gonna Need It”超前实现和自我臆想架构。
   - 🔵 **Refactor (重构与梳理)**：运行 Lint 检查整理风格，并在测试网的保护下保证新写入代码没有破坏此前旧有 Sprint 堆积形成的整体全量测试链路。
9. 如果对项目中遇到了并非简单常规逻辑的技术难题决策，写入到 `artifacts/decisions/ADR-xxx.md` (自动升号) 并将它与前文的测试覆盖结果写入合同结束处备案。
10. 在 `artifacts/handoff.md` 中标明 Generator 的 Sprint 构建任务已提交交付。并等待（或直接唤起转接） `/qa` 评审。
