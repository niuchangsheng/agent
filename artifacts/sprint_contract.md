# Sprint 4 验收合同

## 实现范围 (Scope)
- **后端 (FastAPI)**: 实现 `/api/v1/tasks/{task_id}/dag-tree` 组装树形接口。该接口将扫描某个 Task 所有的 Trace，依照 `parent_trace_id` 关系将扁平数据库记录在内存中组装成标准树形嵌套结构（DAG Tree），以便于前端回溯遍历。
- **前端 (React/Vite)**: 引入 `mermaid` NPM 包。构建一个新的界面组件 `<PlaybackTree />`，负责发起 `dag-tree` 抓取请求，将拿到的一组具有因果依赖的 Trace 转换为 `graph TD` 语法的 Mermaid 文本，并渲染为有向无环交互回溯分叉树图。

## TDD 测试验收标准 (Acceptance Criteria)

### 【红线约束检测】 - Evaluator 视角自我协商校验项
*(自我校验：生成多层嵌套 DAG 时最容易发生死循环或者孤岛节点丢弃。必须在 Red 阶段制造复杂的：一个失败后重试的分支，随后分支再度分叉的数据模型！并在后端断言嵌套正确。)*

### 后端要求 (Backend / pytest)
- **[ ] 测试 1: DAG 复杂节点组装能力**
  - 在 SQLite 测试内存库中手动硬编码注入 4条具有多级父子依赖的 Traces：一条 Root，两条平级的子分支（一条失败，一条成功），以及成功支线下的子叶节点。
  - 访问 `GET /api/v1/tasks/{id}/dag-tree` 必须精准校验返回的 JSON 层级，确保长度与深度完美贴合。
  
### 前端要求 (Frontend / Vitest + RTL)
- **[ ] 测试 1: 树形数据到 Mermaid 语法的翻译**
  - 编写专门针对 `PlaybackTree` 内的数据解析独立测试。模拟一组树形 JSON，断言它的解析函数必定会输出如 `A-->B` 以及区分节点颜色的样式（成功节点绿色，失败红色）合法语句串。
- **[ ] 测试 2: Mermaid SVG 容器就位**
  - 测试渲染挂载过程，检测界面中是否存在标识 `mermaid` 解析目的地的 `<pre class="mermaid" ...>` 容器标记。

## 交付完成标准
- [x] 测试用例涵盖边缘：如查询一个完全还没生成 trace 的任务时，后端平滑返回空数组 `[]`，前端予以友好空态提示。
- [x] 后端通过 `tests/test_dag.py`。
- [x] 前端渲染通过 `tests/PlaybackTree.test.tsx`。
- [x] 遵守 ADR 记录相关渲染折中方案。（见 ADR-004）
