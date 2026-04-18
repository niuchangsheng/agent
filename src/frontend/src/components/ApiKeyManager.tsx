import { useEffect, useState } from 'react';

interface APIKey {
  id: number;
  name: string;
  permissions: string[];
  created_at: string;
  expires_at: string | null;
  is_active: boolean;
}

interface NewKeyResult {
  id: number;
  key: string;
  name: string;
  permissions: string[];
  created_at: string;
  expires_at: string | null;
}

interface AuditLog {
  id: number;
  user_id: number | null;
  action: string;
  resource: string;
  timestamp: string;
  ip_address: string | null;
}

export default function ApiKeyManager() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyPermissions, setNewKeyPermissions] = useState({
    read: true,
    write: true,  // 默认开启 write 权限，以便创建项目
    admin: false
  });
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [showCopyConfirm, setShowCopyConfirm] = useState(false);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchKeys();
    fetchAuditLogs();
  }, []);

  const fetchKeys = async () => {
    try {
      const res = await fetch('/api/v1/auth/api-keys');
      if (res.ok) {
        const data = await res.json();
        setKeys(data);
      }
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch('/api/v1/audit-logs');
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();

    const permissions: string[] = [];
    if (newKeyPermissions.read) permissions.push('read');
    if (newKeyPermissions.write) permissions.push('write');
    if (newKeyPermissions.admin) permissions.push('admin');

    try {
      const res = await fetch('/api/v1/auth/api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newKeyName,
          permissions
        })
      });

      if (res.ok) {
        const data: NewKeyResult = await res.json();
        setGeneratedKey(data.key);
        // 同时保存到 localStorage 供其他组件使用
        localStorage.setItem('api_key', data.key);
        setNewKeyName('');
        setNewKeyPermissions({ read: true, write: false, admin: false });
        fetchKeys();
      }
    } catch (err) {
      console.error('Failed to create API key:', err);
    }
  };

  const handleDeleteKey = async (id: number) => {
    if (!confirm('确认删除此 API Key？此操作不可恢复。')) return;

    try {
      const res = await fetch(`/api/v1/auth/api-keys/${id}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        fetchKeys();
      }
    } catch (err) {
      console.error('Failed to delete API key:', err);
    }
  };

  const copyToClipboard = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey);
      setShowCopyConfirm(true);
      setTimeout(() => setShowCopyConfirm(false), 2000);
    }
  };

  const formatTimestamp = (ts: string) => {
    return new Date(ts).toLocaleString('zh-CN');
  };

  return (
    <div className="space-y-6">
      {/* 创建新 Key */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h2 className="text-xl font-semibold text-cyan-400 mb-4">创建 API Key</h2>
        <form onSubmit={handleCreateKey} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Key 名称</label>
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="例如：Deployment-Key"
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded text-slate-300 focus:outline-none focus:border-cyan-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-2">权限</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newKeyPermissions.read}
                  onChange={(e) => setNewKeyPermissions(prev => ({ ...prev, read: e.target.checked }))}
                  className="w-4 h-4 rounded border-slate-600 text-cyan-500 focus:ring-cyan-500"
                />
                <span className="text-slate-300">读取 (Read)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newKeyPermissions.write}
                  onChange={(e) => setNewKeyPermissions(prev => ({ ...prev, write: e.target.checked }))}
                  className="w-4 h-4 rounded border-slate-600 text-amber-500 focus:ring-amber-500"
                />
                <span className="text-slate-300">写入 (Write)</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newKeyPermissions.admin}
                  onChange={(e) => setNewKeyPermissions(prev => ({ ...prev, admin: e.target.checked }))}
                  className="w-4 h-4 rounded border-slate-600 text-red-500 focus:ring-red-500"
                />
                <span className="text-slate-300">管理员 (Admin)</span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded font-medium transition-colors"
          >
            生成 API Key
          </button>
        </form>

        {generatedKey && (
          <div className="mt-4 p-4 bg-emerald-900/30 border border-emerald-500/50 rounded">
            <p className="text-emerald-400 font-medium mb-2">⚠️ 重要：这是您唯一一次能看到完整的 API Key</p>
            <div className="flex gap-2">
              <code className="flex-1 px-3 py-2 bg-slate-900 rounded text-emerald-300 font-mono text-sm break-all">
                {generatedKey}
              </code>
              <button
                onClick={copyToClipboard}
                className="px-3 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-sm font-medium transition-colors"
              >
                {showCopyConfirm ? '已复制!' : '复制'}
              </button>
            </div>
            <p className="text-slate-400 text-sm mt-2">请妥善保存，刷新页面后将无法再次查看。</p>
          </div>
        )}
      </div>

      {/* API Key 列表 */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <h2 className="text-xl font-semibold text-cyan-400 mb-4">API Key 列表</h2>
        <div className="space-y-2">
          {keys.length === 0 ? (
            <p className="text-slate-500 text-sm">暂无 API Key</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-slate-400 border-b border-slate-700">
                  <th className="text-left py-2 font-medium">名称</th>
                  <th className="text-left py-2 font-medium">权限</th>
                  <th className="text-left py-2 font-medium">创建时间</th>
                  <th className="text-left py-2 font-medium">过期时间</th>
                  <th className="text-left py-2 font-medium">状态</th>
                  <th className="text-right py-2 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                {keys.map(key => (
                  <tr key={key.id} className="border-b border-slate-700/50">
                    <td className="py-2 text-slate-300">{key.name}</td>
                    <td className="py-2">
                      <div className="flex gap-1">
                        {key.permissions.map(perm => (
                          <span
                            key={perm}
                            className={`px-2 py-0.5 rounded text-xs font-medium ${
                              perm === 'admin' ? 'bg-red-500/20 text-red-400' :
                              perm === 'write' ? 'bg-amber-500/20 text-amber-400' :
                              'bg-cyan-500/20 text-cyan-400'
                            }`}
                          >
                            {perm.toUpperCase()}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-2 text-slate-400">{formatTimestamp(key.created_at)}</td>
                    <td className="py-2 text-slate-400">
                      {key.expires_at ? formatTimestamp(key.expires_at) : '永不过期'}
                    </td>
                    <td className="py-2">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        key.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {key.is_active ? '活跃' : '已禁用'}
                      </span>
                    </td>
                    <td className="py-2 text-right">
                      <button
                        onClick={() => handleDeleteKey(key.id)}
                        className="text-red-400 hover:text-red-300 text-sm font-medium"
                      >
                        删除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 审计日志 */}
      <div className="bg-slate-800/50 rounded-lg p-6 border border-slate-700">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-cyan-400">审计日志</h2>
          <button
            onClick={fetchAuditLogs}
            className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition-colors"
          >
            刷新
          </button>
        </div>
        {loading ? (
          <p className="text-slate-500 text-sm">加载中...</p>
        ) : auditLogs.length === 0 ? (
          <p className="text-slate-500 text-sm">暂无审计日志</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400 border-b border-slate-700">
                <th className="text-left py-2 font-medium">时间</th>
                <th className="text-left py-2 font-medium">操作</th>
                <th className="text-left py-2 font-medium">资源</th>
                <th className="text-left py-2 font-medium">用户 ID</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map(log => (
                <tr key={log.id} className="border-b border-slate-700/50">
                  <td className="py-2 text-slate-400">{formatTimestamp(log.timestamp)}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      log.action === 'DELETE' ? 'bg-red-500/20 text-red-400' :
                      log.action === 'PUT' ? 'bg-amber-500/20 text-amber-400' :
                      'bg-cyan-500/20 text-cyan-400'
                    }`}>
                      {log.action}
                    </span>
                  </td>
                  <td className="py-2 text-slate-300 font-mono text-xs">{log.resource}</td>
                  <td className="py-2 text-slate-400">{log.user_id ?? '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
