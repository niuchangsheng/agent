# Sprint 5 验收合同

## 实现范围 (Scope)
- **后端 (FastAPI)**: 实现 `/api/v1/tasks/{task_id}/generate-adr` 端点。通过对给定 Task 遍历出成功路径（`is_success=True`）以及失败试错（`is_success=False`），模拟 AI 沉淀过程（Mock LLM API 以避免引入外部额度依赖），自动生硬一段技术复盘文档。
- 将产出的 ADR 文档实体不仅落入 SQLite 的 `Adr` 库表，同时在物理执行侧输出 `artifacts/decisions/ADR-xxx.md`。

## TDD 测试验收标准 (Acceptance Criteria)

### 【红线约束检测】 - Evaluator 视角自我协商校验项
*(自我校验：生成器必须能够访问到真实的磁盘 `artifacts/decisions` 目录并有写权限。测试用例必须能够真实提取到伪造的一条失败和成功的 Trace 摘要。)*

### 后端要求 (Backend / pytest)
- **[ ] 测试 1: ADR 的端点集成生成及入库**
  - 利用 fixture 中的假任务，触发请求。
  - 断言能成功返回 200，并解析到的 `generated_markdown_payload` 中带有该任务中曾经发生过的 `Raw Objective` 及成功节点的简略片段。
- **[ ] 测试 2: 文件系统的联动下沉**
  - 触发上述相同的生成操作后，在隔离的 `tmp_path` (使用 pytest fixture 防止污染真实磁盘) 中能够查询到新鲜生成的 `ADR-[id].md` 存在。

## 交付完成标准
- [x] 测试用例涵盖 `test_adr_generator.py` 并通过。
- [x] 代码架构中将业务逻辑与具体的 `FileSystemWriter` 进行了解耦（基于 ADR_STORAGE_PATH 环境隔绝）。
- [x] 代码不留遗留瑕疵，准备接受最终的 `/release` 洗礼全线跑通。
