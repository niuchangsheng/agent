---
description: 继续执行长期运行任务（长循环构建）
---

# /run-continue - 长周期任务继续执行

**适用场景**：从上一次中断处继续执行未完成的 Sprint，适用于长期迭代开发。

## 执行流程

1. **状态检测**：执行 `node .claude/hooks/run-status-check.js` 显示当前进度

2. **读取手尾文档**：解析 `artifacts/handoff.md` 获取：
   - 最后执行到的 Sprint 编号
   - 是否有阻塞错误需要处理
   - 关键决策摘要

3. **继续执行**：
   - 若有 `[!]` 阻塞的 Sprint → 优先处理
   - 否则按顺序执行第一个 `[ ]` 待办 Sprint

4. **持久化**：
   - 每个 Sprint 完成后自动 `git add -A && git commit`
   - 更新 `handoff.md` 时间戳和状态

## 与 /run 的区别

| 特性 | /run | /run-continue |
|------|------|---------------|
| 适用场景 | 完整工作流 | 从中断处继续 |
| 状态检测 | 简单 | 详细 + handoff 解析 |
| 提交频率 | 每个版本 | 每个 Sprint |
| 输出 verbosity | 标准 | 详细 |

---

**注意**：此命令设计为 long-running task，可以在后台持续执行数小时。
