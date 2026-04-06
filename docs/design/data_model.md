# SECA 数据模型体系设计

## 1. 全局图谱
一切根源追溯于 Task (一次指令执行)。而 Agent 与底层的攻防博弈将被细化碎片在 Trace 表级。

```mermaid
erDiagram
    PROJECT ||--o{ TASK : manages
    TASK ||--o{ TRACE : records
    TASK ||--o{ ADR : generates
    TRACE ||--o{ DIAGNOSTIC_EVENT : triggers
    
    PROJECT {
        string id PK
        string name
        string target_repo_path "所要管控和诊断的物理目录位"
    }
    
    TASK {
        string id PK
        string project_id FK
        text raw_objective "用户的原语目的"
        string status "PENDING|RUNNING|ANALYZING|DONE|FAILED"
        datetime started_at
    }
    
    TRACE {
        string id PK
        string task_id FK
        string parent_trace_id FK "【重核】支撑逻辑回溯图的基础因果链指针"
        string agent_role "谁在发起的思考"
        text perception_log "观测与环境收集的数据"
        text reasoning_log "权衡策略推导数据"
        text applied_patch "做出的 DIFF 或者 Command"
        boolean is_success "这步执行沙箱评价是否成功"
    }
    
    DIAGNOSTIC_EVENT {
        string id PK
        string trace_id FK "这属于哪一步踩雷产生的拦截"
        string error_type "SYN|TIMEOUT|HUNG|LOGIC"
        text raw_stderr "生胶囊级抓取"
    }
    
    ADR {
        string id PK
        string task_id FK
        string brief_title
        text generated_markdown_payload "产出的制度全文结构资产"
    }
```

## 2. 数据字典流传点核说
- `TRACE.parent_trace_id`: 此处若为空则代表这步是从 Task根级开启的首层探讨。若尝试修 A bug 失败，Agent 退回到 A 节点前重新选择修 B，则它派生的子类也会同样以该父节点指向自己，实现 DAG 有向无环图关联，这是产品 Playback 回放流的心脏字段。
