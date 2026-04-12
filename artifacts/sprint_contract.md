# Sprint 8 验收合同：基础认证与权限

## 合同签署方
- **需求方**: product_spec.md Feature 7
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### 后端交付物
1. **数据模型**:
   - `APIKey` 表：存储 API 密钥及其权限
     - `key_hash` - 哈希后的密钥
     - `permissions` - 权限列表 (read, write, admin)
     - `created_at` / `expires_at` - 时间戳
   - `AuditLog` 表：审计日志
     - `user_id` - 用户/API Key ID
     - `action` - 操作类型
     - `resource` - 资源路径
     - `timestamp` - 操作时间
     - `ip_address` - IP 地址

2. **中间件与装饰器**:
   - `APIKeyMiddleware` - 验证 API Key
   - `require_permission` - 权限装饰器

3. **API 端点**:
   - `POST /api/v1/auth/api-keys` - 创建 API Key
   - `GET /api/v1/auth/api-keys` - 列出 API Keys
   - `DELETE /api/v1/auth/api-keys/{id}` - 删除 API Key
   - 所有现有写操作端点添加认证保护

### 前端交付物
1. **API Key 管理面板**:
   - 创建/删除 API Key
   - 权限选择 (Read/Write/Admin)
   - Key 显示 (仅创建时显示一次)

2. **认证集成**:
   - 登录态持久化 (localStorage)
   - 401/403 错误处理
   - 请求自动携带 API Key

## 验收测试清单

### TDD 测试用例 (必须全部通过)

#### Red 路径测试 (边界/异常)
- [ ] `test_no_api_key_returns_401` - 无 Key 请求返回 401
- [ ] `test_invalid_api_key_returns_401` - 无效 Key 返回 401
- [ ] `test_readonly_key_cannot_write` - 只读 Key 不能写操作
- [ ] `test_expired_api_key_rejected` - 过期 Key 被拒绝

#### Green 路径测试 (Happy Path)
- [ ] `test_api_key_creation` - 创建 API Key
- [ ] `test_api_key_list` - 列出 API Keys
- [ ] `test_api_key_delete` - 删除 API Key
- [ ] `test_write_operation_with_valid_key` - 有效 Key 可执行写操作
- [ ] `test_audit_log_created_on_write` - 写操作创建审计日志

#### 集成测试
- [ ] `test_middleware_protects_all_write_routes` - 中间件保护所有写路由

## 技术约束
- MVP 仅支持单层级 API Key 认证
- 密钥必须哈希存储 (bcrypt/sha256)
- 审计日志记录所有写操作

## 完成定义
- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-7 的测试
- [ ] handoff.md 更新完成
