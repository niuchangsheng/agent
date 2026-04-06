# SECA 系统架构设计

## 1. 架构目标
贯彻 "意图胜出代码" (Intent over Code) 的核心哲学。建立隔离观察室和全视监控台体系：以白盒形式将大型智能体进行沙盒控制与透视化。

## 2. 工具链硬选型
- **应用客户端 (Dashboard)**: React + Vite + TailwindCSS + Zustand 状态网。极致的 Hacker 风与现代毛玻璃（Glassmorphism）极简质感。
- **接入与流控核心 (Core API)**: FastAPI + Pydantic (Type Hints 保卫战)。选用强类型。
- **持久化记录底座 (State Storage)**: SQLModel + aiosqlite (首置 MVP 无痛本地方案，通过 ORM 为迁移 PostgreSQL 留后门)。
- **信令协议 (Communication)**: SSE (Server-Sent Events) 纯推流应用层；REST 接收。

## 3. C4 架构容器分布

```mermaid
C4Context
    title SECA (Self-Evolving Coding Agent) 容器分布
    
    Person(tech_lead, "技术总控 TL", "调配与接管架构巡检工作 / 旁观回放审判")
    
    System_Boundary(seca_system, "SECA 核心架构环") {
        Container(webapp, "监控台与回放器 (Web App)", "React TypeScript", "内省视图，Trace流呈现，分叉图绘制")
        Container(api_gateway, "管控网关 (Orchestrator)", "FastAPI", "API 接受池 / 协同 Agent 发起 / SSE发还流")
        
        Container(harness, "截断与捕捉沙箱 (Sandbox)", "Python Subprocess", "隔离挂载运行目标脚本，强制捕获原生的 std:err/out 与 exit code")
        
        ContainerDb(database, "知识与状态库", "SQLite", "以结构化 JSON 的形体记录下发下去的任务，Trace思考痕迹和分叉 ID ")
    }
    
    Rel(tech_lead, webapp, "指令投放 / Trace围观 / 知识考古", "HTTPS")
    Rel(webapp, api_gateway, "状态问询 / 接受打字机回传流", "REST / WSS(SSE)")
    Rel(api_gateway, harness, "封箱推送验证脚本与命令流")
    Rel(harness, api_gateway, "打回原始现场快照及错误堆栈")
    Rel(api_gateway, database, "关联存储逻辑链关系并存档")
```

## 4. 核心实现挑战及架构容忍度
MVP 版本最大的妥协：**沙箱防溢性**。Docker 级别的真物理隔离由于守护进程（Daemon）接管繁复并损耗 I/O 和计算等待，为保证轻量化迭代演进，前期全盘使用 Node/Python Subprocess 来实现包裹沙盒。这对恶意循环等系统调用具有一定妥协，但在目前为足够有效。
