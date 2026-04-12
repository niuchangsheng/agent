# SECA Harness Engineer 配置

## 角色定义
- **Planner** (产品架构师): `.claude/agents/planner.md`
- **Generator** (TDD 工程师): `.claude/agents/generator.md`
- **Evaluator** (QA 评估官): `.claude/agents/evaluator.md`

## 工作流命令
- `/plan` - 执行 Planner 角色，生成产品规格
- `/build` - 执行 Generator 角色，TDD 方式开发
- `/qa` - 执行 Evaluator 角色，QA 评审打分
- `/run` - 自动调度器，驱动 规划→构建→QA 闭环
- `/release` - 项目结项交付

##  artifacts 目录结构
- `artifacts/product_spec.md` - 产品规格说明书
- `artifacts/sprint_contract.md` - Sprint 验收合同
- `artifacts/qa_feedback.md` - QA 评审反馈
- `artifacts/handoff.md` - 交接文档
- `artifacts/decisions/` - ADR 决策记录
- `artifacts/release_report.md` - 结项报告

## 开发规范
- 前端：React + TypeScript + Vite + Vitest
- 后端：FastAPI + Python + SQLModel + pytest
- TDD 流程：Red → Green → Refactor
