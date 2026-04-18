# Sprint 18 验收合同：镜像优化与 Trace 回放

## 合同签署方
- **需求方**: product_spec.md Feature 21, Feature 24 (Sprint 18)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能概述
本 Sprint 包含两个独立 Feature：
1. **Feature 21**: 镜像预拉取优化 - 后端调度器 + API
2. **Feature 24**: Trace 回放增强 - 前端播放器组件

---

## Part A: Feature 21 - 镜像预拉取优化

### 后端单元测试 (`src/backend/tests/test_image_prepull.py`) - 6 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `test_image_config_get` | GET /api/v1/images 返回预配置镜像列表 | [ ] |
| `test_image_config_add` | POST /api/v1/images 添加新镜像配置 | [ ] |
| `test_image_status_check` | 检查镜像本地状态（ready/pulling/missing） | [ ] |
| `test_image_prepull_trigger` | 手动触发镜像预拉取 | [ ] |
| `test_image_wait_queue` | 镜像未就绪时任务进入等待队列 | [ ] |
| `test_image_unavailable_error` | 镜像不可用时返回错误 | [ ] |

### API 端点设计

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/images` | GET | 获取镜像配置列表及状态 |
| `/api/v1/images` | POST | 添加镜像配置 |
| `/api/v1/images/{name}/pull` | POST | 触发镜像拉取 |
| `/api/v1/images/{name}/status` | GET | 获取镜像状态 |

### 数据模型

```python
class ImageConfig(SQLModel, table=True):
    id: int
    name: str  # 如 "alpine:3.18"
    status: str  # "ready", "pulling", "missing", "failed"
    last_pull_at: datetime
    created_at: datetime
```

---

## Part B: Feature 24 - Trace 回放增强

### 前端单元测试 (`src/frontend/tests/TracePlayback.test.tsx`) - 8 tests

| 测试项 | 验收标准 | 状态 |
|--------|----------|------|
| `renders playback controls` | 显示播放/暂停、时间轴、倍速选择器 | [ ] |
| `displays trace steps from API` | 显示 Trace 步骤列表 | [ ] |
| `play_pause_toggle_works` | 点击播放/暂停切换状态 | [ ] |
| `speed_selector_changes_speed` | 倍速选择器切换 0.5x/1x/2x/5x | [ ] |
| `timeline_slider_navigation` | 时间轴滑块导航到指定步骤 | [ ] |
| `current_step_highlighted` | 当前步骤高亮显示 | [ ] |
| `handles empty_trace` | 无 Trace 时显示空状态 | [ ] |
| `sends API key in headers` | 请求携带 API Key | [ ] |

### 组件 Props

```typescript
interface TracePlaybackProps {
  taskId: number;
  autoPlay?: boolean;
  defaultSpeed?: number;  // 0.5, 1, 2, 5
}
```

### UI 设计规范

- 时间轴: 滑块控件，显示总步数和当前位置
- 倍速选择器: 下拉菜单 0.5x/1x/2x/5x
- 播放/暂停按钮: 图标按钮
- 步骤列表: 垂直滚动列表，当前步骤高亮（bg-cyan-500/20）
- Glassmorphism 风格: `backdrop-blur-md bg-slate-900/50 border-cyan-500/30`

---

## 完成定义

- [ ] Feature 21 后端测试全部通过 (6 tests)
- [ ] Feature 24 前端测试全部通过 (8 tests)
- [ ] Glassmorphism 风格与其他组件一致
- [ ] 回归测试：不破坏 Sprint 1-17.5 的功能
- [ ] TypeScript 编译无错误
- [ ] handoff.md 更新完成

---

## 技术备注

### Feature 21 实现要点
- 镜像预拉取使用后台任务异步执行
- 状态检测使用 Docker SDK (`docker.images.get()`)
- 拉取失败时记录错误日志，不影响其他镜像

### Feature 24 实现要点
- 复用现有 `/api/v1/tasks/{id}/dag-tree` API
- 添加 `/api/v1/tasks/{id}/traces` 获取完整 Trace 列表
- 时间轴基于步骤索引，支持跳跃导航

---

**签署时间**: 2026-04-19
**Generator 签名**: Sprint 18 开发启动