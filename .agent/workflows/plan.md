---
description: 执行 Planner 角色，进行产品与架构规划
---

1. 读取 `skills/planner/SKILL.md` 获取作为产品架构师的深度指导原则。
2. 尝试读取 `artifacts/handoff.md`（若存在），以恢复先前的对话上下文。
3. 读取项目根目录的 `README.md`，理解项目的愿景、核心哲学及功能要求。
4. 从抽象描述中抽离出系统架构所需的模块，并生成全套设计文档到 `docs/design/`：
   - `architecture.md`: 系统架构设计（C4 图 + 模块职责 + 技术选型理由）
   - `data_model.md`: 数据模型设计（实体关系 + ER 图）
   - `api_design.md`: API 接口设计（RESTful 路由 + 请求/响应示例）
   - `ui_wireframes.md`: UI 线框图 / 页面流转
5. 将模块功能拆解为独立的 Feature（并为每个标注复杂度、MVP必要性、风险与降级方案）。将这些 Feature 组织成有明确先后顺序的 Sprint 周期分解，并在规范文件的末尾附上整个项目的最终验收标准（DoD）。
6. 将上一步产生的整体规格内容作为《产品规格说明书》写入到 `artifacts/product_spec.md`。
7. 创建更新 `artifacts/handoff.md`，记录此次 Planner 执行结果及技术决策定调，并说明下一步动作。
8. 提示用户对上述一系列文档展开审阅，如无异议，可使用 `/run` 启动整个大运转闭环。
