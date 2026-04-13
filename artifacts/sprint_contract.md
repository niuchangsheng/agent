# Sprint 10 验收合同：API Key 加密存储增强

## 合同签署方
- **需求方**: product_spec.md Feature 9 (Sprint 10)
- **执行方**: Generator (TDD 工程师)
- **验收方**: Evaluator (QA 评审官)

## 功能范围

### 背景
Sprint 8 已实现 API Key 的 SHA256 哈希存储和过期验证。Sprint 10 升级为更安全的 bcrypt 哈希算法，增加暴力破解难度。

### 后端交付物

1. **依赖库**:
   - `bcrypt` 库集成（替代 SHA256）

2. **认证模块升级**:
   - `hash_api_key()` 升级为 bcrypt 哈希
   - `verify_api_key()` 使用 bcrypt 验证
   - 保持现有 API 接口不变

3. **数据模型** (无需变更):
   - `APIKey.key_hash` 字段存储 bcrypt 哈希
   - `APIKey.expires_at` 字段已存在，支持过期验证

### API 端点 (保持不变)
- `POST /api/v1/auth/api-keys` - 创建 API Key（返回明文仅一次）
- `GET /api/v1/auth/api-keys` - 列出 API Keys（不返回哈希）
- `DELETE /api/v1/auth/api-keys/{id}` - 删除 API Key

## 验收测试清单

### TDD 测试用例 (必须全部通过)

#### bcrypt 哈希测试
- [ ] `test_bcrypt_hash_produces_different_hashes_for_same_input` - bcrypt 随机盐产生不同哈希
- [ ] `test_bcrypt_verify_valid_key` - bcrypt 验证有效 Key
- [ ] `test_bcrypt_verify_invalid_key` - bcrypt 拒绝无效 Key
- [ ] `test_bcrypt_hash_length` - bcrypt 哈希长度正确（60 字符）

#### 过期验证测试
- [ ] `test_expired_api_key_rejected` - 过期 Key 被拒绝（401）
- [ ] `test_api_key_with_future_expiry_accepted` - 未过期 Key 被接受
- [ ] `test_api_key_without_expiry_accepted` - 无过期时间 Key 被接受

#### 安全测试
- [ ] `test_plain_key_never_stored` - 明文 Key 永不存储
- [ ] `test_create_response_shows_key_once` - 创建响应仅显示一次明文
- [ ] `test_list_does_not_expose_hash` - 列表接口不暴露哈希

#### 回归测试 (Sprint 8)
- [ ] `test_no_api_key_returns_401` - 无 Key 返回 401
- [ ] `test_invalid_api_key_returns_401` - 无效 Key 返回 401
- [ ] `test_readonly_key_cannot_write` - 只读 Key 不能写
- [ ] `test_write_operation_with_valid_key` - 有效 Key 可写操作

## 技术约束

1. **bcrypt 参数**:
   - rounds=12（平衡安全性和性能）
   - 随机盐自动生成

2. **向后兼容**:
   - 现有 API Key 无需迁移（新 Key 使用 bcrypt）
   - 或提供迁移脚本（可选）

3. **YAGNI 原则**:
   - 不实现密钥轮换
   - 不实现多 Key 管理

## 完成定义

- [ ] 所有测试用例编写完成 (Red)
- [ ] 所有测试用例通过 (Green)
- [ ] Lint 检查无警告
- [ ] 不破坏现有 Sprint 1-9 的测试
- [ ] handoff.md 更新完成

## 交付文件清单

- [ ] `src/backend/app/auth.py` - 升级为 bcrypt
- [ ] `src/backend/tests/test_auth.py` - 更新测试
- [ ] `requirements.txt` (或 pyproject.toml) - 添加 bcrypt 依赖
