---
description: 自动驱动规划、构建、QA 测试闭环的永动迭代调度器
---

# /run - 永动迭代调度器

## 核心规则（必须遵守）

1. **每个 Sprint 完成后必须：**
   - 更新 `artifacts/handoff.md`（最新进度、时间戳）
   - 执行 `git add -A && git commit -m "chore(sprint N): ..."`
   - 然后才能继续下一个 Sprint

2. **每轮 build→qa 后评估 Context：**
   - 如果已经执行了 1 个 Sprint → 停止，提示用户开启新 session
   - 如果还有 Sprint 待执行 → 输出："请执行 `claude -p '/run'` 开启新 session 继续"

## 执行流程

### 1. 检测 product_spec.md
若不存在 → 先转跑 `/plan` 工作流。

### 2. 版本状态检测
解析 `product_spec.md` 中的"版本历史"表：
- 若所有版本状态均为 `✅ 已完成` → 调用 `/plan` 规划新版本
- 若存在 `🔄 规划中` 的 Sprint → 执行步骤 3

### 3. 执行单个 Sprint（仅此一个）
- 调用 `/build` 执行 TDD 开发
- 调用 `/qa` 进行评审
- **必须**更新 `handoff.md`
- **必须** `git commit`
- **然后停止**，输出：
  ```
  ✅ Sprint N 完成
  ⚡ 为避免 context 超限，请开启新 session 继续
  执行：claude -p '/run'
  ```

### 4. 熔断机制
若 Sprint 连续 3 次被 QA 打回：
- 写入 `handoff.md`
- `git commit` 留存状态
- 停止并求助

---

## 状态标记
- `✅ 已完成` - 版本所有 Sprint 通过 QA
- `🔄 规划中` - Sprint 已定义待执行
- `⏳ 进行中` - Sprint 正在开发

## 跨会话
- 状态存在 `handoff.md` 和 git 历史
- 新 session 执行 `/run` 自动继续
