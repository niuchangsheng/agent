# SECA 数据模型设计

## 1. 实体关系概述

SECA 的核心业务对象围绕着**项目层级 (Project)**、**任务指令 (Task)** 和底层原子单位**执行轨迹 (Trace)** 构建，为后续复杂的错误根因回放及架构决策关联提供结构化基础。

```mermaid
erDiagram
    PROJECT ||--o{ TASK : contains
    TASK ||--o{ TRACE : records
    TASK ||--o{ ADR : generates
    TRACE ||--o{ DIAGNOSTIC_EVENT : triggers
    
    PROJECT {
        string id PK
        string name
        string description
        string local_repo_path
        datetime created_at
    }
    
    TASK {
        string id PK
        string project_id FK
        string objective
        string status "PENDING|RUNNING|EVALUATING|DONE|FAILED"
        datetime created_at
        datetime updated_at
    }
    
    TRACE {
        string id PK
        string task_id FK
        string parent_trace_id FK "支持回放树结构分叉"
        string agent_role "planner|generator|evaluator"
        string prompt_snapshot
        text perception_log
        text reasoning_log
        text generated_code
        string execution_result 
        boolean is_success
        datetime timestamp
    }
    
    DIAGNOSTIC_EVENT {
        string id PK
        string trace_id FK
        string error_type "SYNTAX|RUNTIME|TEST_FAIL|LINT"
        text raw_stderr
        text injected_improvement
    }
    
    ADR {
        string id PK
        string task_id FK
        string title
        text decision
        text context_and_consequences
        string status "PROPOSED|ACCEPTED|REJECTED"
        datetime timestamp
    }
```

## 2. 字段生命周期说明
- `TRACE.parent_trace_id` 构成了系统能以树状图形回溯展示（Post-mortem Playback）的基石。在试错中，每当产生代码错误并回退修正时，在此节点派生新的 trace 子节点即可。
- `DIAGNOSTIC_EVENT` 为动态元优化提供基础，该表统计了 Agent 跌倒重灾区错误情况，能供机器学习长期反馈分析（资本效率与诊断 ROI）。
