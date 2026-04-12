# Sprint 6 验收合同：配置管理中心

## 合同签署方
- **需求方**: product_spec.md Feature 5
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### 后端交付物
1. **数据模型**: `ProjectConfig` 表，包含：
   - `project_id` (FK) - 关联 Project
   - `sandbox_timeout_seconds` - 沙箱超时限制 (默认 30s)
   - `max_memory_mb` - 最大内存配额 (默认 512MB)
   - `environment_variables` - JSON 格式的环境变量
   - `created_at` / `updated_at` - 时间戳

2. **API 端点**:
   - `GET /api/v1/projects/{id}/config` - 获取配置
   - `PUT /api/v1/projects/{id}/config` - 更新配置
   - `POST /api/v1/projects/{id}/config` - 创建配置

### 前端交付物
1. **配置管理面板 UI**:
   - 在 Dashboard 中添加配置入口
   - 环境变量编辑器 (Key-Value 对)
   - 沙箱配额滑块控件 (超时 1-60s, 内存 128-2048MB)

2. **集成验证**:
   - 配置修改后新任务立即生效

## 验收测试清单

### TDD 测试用例 (全部通过 ✅)

#### Red 路径测试 (边界/异常)
- [x] `test_config_not_found_returns_404` - 项目不存在时返回 404
- [x] `test_config_create_invalid_project_id` - 无效 project_id 创建失败
- [x] `test_config_timeout_out_of_range` - 超时超出范围验证
- [x] `test_config_memory_out_of_range` - 内存超出范围验证

#### Green 路径测试 (Happy Path)
- [x] `test_config_create_and_get` - 创建并获取配置
- [x] `test_config_update` - 更新配置
- [x] `test_config_isolation` - 3 个并发任务各自遵循独立配额

#### 前端测试
- [x] `ConfigPanel 应当渲染配置面板标题`
- [x] `ConfigPanel 应当显示沙箱超时滑块`
- [x] `ConfigPanel 应当显示内存配额滑块`
- [x] `ConfigPanel 应当能添加环境变量`
- [x] `ConfigPanel 应当能保存配置`

## 技术约束
- ✅ 配置修改仅对新任务生效，不中断运行中任务
- ✅ 环境变量以 JSON 存储，支持动态键值对
- ✅ 所有端点需要类型验证 (Pydantic)

## 测试结果汇总
- **后端测试**: 20/20 通过 (包含 Sprint 1-5 的回归测试)
- **前端测试**: 12/12 通过

## ADR 记录
- ADR-006: 配置中心数据模型设计 (使用 SQLModel JSON 类型存储环境变量)

## 完成定义
- [x] 所有测试用例编写完成 (Red)
- [x] 所有测试用例通过 (Green)
- [x] Lint 检查无警告
- [x] 不破坏现有 Sprint 1-5 的测试
- [x] handoff.md 更新完成

## 交付状态
✅ **Sprint 6 已完成，准备接受 QA 评审**
