# SECA 系统架构设计

## 1. 架构目标
实现 README 中定义的 "Intent over Code" 理念，提供基于反馈诊断的智能体闭环。本架构明确分离**用户交互层**、**Agent编排控制层**、与**沙箱执行层**。

## 2. 核心技术选型
- **前端（User Interface）**: React 18, Vite, TailwindCSS (现代且高效地搭建拟态设计), Zustand (处理全局状态，特别适合实时通信日志的管理)。
- **后端（Orchestration & API）**: FastAPI (Python), SQLModel/SQLAlchemy (ORM层支持类型完整与异步能力)。
- **持久层**: SQLite (MVP 阶段), 结合 `aiosqlite` 保证非阻塞 IO，可平滑迁移至 PostgreSQL。
- **通信协议**: 数据读写采用 RESTful API，内省任务监控面板全部采用 Server-Sent Events (SSE) 单向推送提升性能。

## 3. C4 架构容器图 (Container Diagram)

```mermaid
C4Context
    title SECA (Self-Evolving Coding Agent) 容器级架构
    
    Person(tech_lead, "Tech Lead / Architect", "发起任务，审查审计Agent思考流与回放")
    
    System_Boundary(seca_system, "SECA 核心系统") {
        Container(webapp, "前端控制台", "React + Vite", "流式渲染内省流，可视化逻辑分叉树")
        Container(api_gateway, "SECA API 服务", "FastAPI", "管理项目任务、提供状态回查、SSE实时推送")
        
        Container(orchestrator, "Agent 编排引擎", "Python SDK", "驱动 Planner, Generator, Evaluator 三角色内循环")
        Container(harness, "Diagnostic Harness (诊断沙箱)", "Subprocess/隔离环境", "按指令拦截输出，采集 Traces 并注入诊断逻辑")
        
        ContainerDb(database, "知识与状态库", "SQLite", "存储 Task, Trace, ADR 等上下文信息")
    }
    
    Rel(tech_lead, webapp, "提交代码指令/查看审计报告", "HTTPS")
    Rel(webapp, api_gateway, "REST API / SSE流", "HTTPS/WSS")
    Rel(api_gateway, orchestrator, "下发任务指令")
    Rel(orchestrator, harness, "驱动运行代码并采集日志", "安全隔离调用")
    Rel(harness, orchestrator, "返回 Traces (stdout/err/结果)")
    Rel(orchestrator, database, "持久化执行路径与决策")
```

## 4. 模块职责划分
- **API 层 / 路由层 `api_router`**: 负责处理鉴权、项目配置信息的 CRUD 和 SSE 流媒体推送池的管理。
- **编排层 `engine`**: 解析并下发 Agent 策略。包含重试/重构、提示词诊断优化循环；维护在长线程任务下的对话上下文长度处理方案。
- **沙箱/Harness 层 `sandbox`**: 提供统一的 `execute_code()` 核心接口。解析代码/Bash命令执行，无侵入式捕获退出码和异常栈，封装为固定结构体对象 `TraceResult` 供编排层做后续推理。
