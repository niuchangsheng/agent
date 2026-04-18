import { useEffect, useState } from 'react';

interface DockerConfig {
  id?: number;
  memory_limit_mb: number;
  cpu_limit: number;
  timeout_seconds: number;
  max_concurrent_containers: number;
}

interface DockerConfigPanelProps {
  onConfigChange?: (config: DockerConfig) => void;
}

const DockerConfigPanel: React.FC<DockerConfigPanelProps> = ({ onConfigChange }) => {
  const [config, setConfig] = useState<DockerConfig>({
    memory_limit_mb: 512,
    cpu_limit: 1,
    timeout_seconds: 60,
    max_concurrent_containers: 3
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);

    const apiKey = localStorage.getItem('api_key') || '';

    fetch('/api/v1/docker-config', {
      headers: {
        'X-API-Key': apiKey
      }
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch Docker config');
        return res.json();
      })
      .then(data => {
        setConfig(data);
      })
      .catch(err => {
        setError(err.message);
      })
      .finally(() => setLoading(false));
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    // 验证配置
    if (config.memory_limit_mb < 64 || config.memory_limit_mb > 4096) {
      setError('Memory limit must be between 64MB and 4096MB');
      setLoading(false);
      return;
    }
    if (config.cpu_limit < 0.5 || config.cpu_limit > 4) {
      setError('CPU limit must be between 0.5 and 4 cores');
      setLoading(false);
      return;
    }
    if (config.timeout_seconds < 10 || config.timeout_seconds > 300) {
      setError('Timeout must be between 10 and 300 seconds');
      setLoading(false);
      return;
    }
    if (config.max_concurrent_containers < 1 || config.max_concurrent_containers > 10) {
      setError('Max concurrent containers must be between 1 and 10');
      setLoading(false);
      return;
    }

    const apiKey = localStorage.getItem('api_key') || '';

    try {
      const res = await fetch('/api/v1/docker-config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
        body: JSON.stringify(config)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to save config');
      }

      const savedConfig = await res.json();
      setConfig(savedConfig);
      setSuccess('Docker configuration saved successfully!');
      onConfigChange?.(savedConfig);

      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save config');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-900/20">
      <h2 className="text-xl mb-4 border-b border-slate-700 pb-2 text-white flex justify-between">
        <span>🐳 Docker Sandbox Configuration</span>
      </h2>

      {loading && !config && (
        <div className="text-slate-500 animate-pulse">Loading configuration...</div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-emerald-900/30 border border-emerald-500/50 rounded text-emerald-300 text-sm">
          {success}
        </div>
      )}

      <div className="space-y-4">
        {/* 内存限制设置 */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">
            Memory Limit (MB): {config.memory_limit_mb}MB
          </label>
          <input
            type="range"
            min="64"
            max="4096"
            step="64"
            value={config.memory_limit_mb}
            onChange={(e) => setConfig({ ...config, memory_limit_mb: Number(e.target.value) })}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>64MB</span>
            <span>4096MB</span>
          </div>
          {config.memory_limit_mb < 64 || config.memory_limit_mb > 4096 ? (
            <span className="text-red-400 text-xs">⚠️ Must be between 64MB and 4096MB</span>
          ) : (
            <span className="text-emerald-400 text-xs">✓ Valid range</span>
          )}
        </div>

        {/* CPU 限制设置 */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">
            CPU Limit (cores): {config.cpu_limit}
          </label>
          <input
            type="range"
            min="0.5"
            max="4"
            step="0.5"
            value={config.cpu_limit}
            onChange={(e) => setConfig({ ...config, cpu_limit: Number(e.target.value) })}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>0.5</span>
            <span>4</span>
          </div>
          {config.cpu_limit < 0.5 || config.cpu_limit > 4 ? (
            <span className="text-red-400 text-xs">⚠️ Must be between 0.5 and 4 cores</span>
          ) : (
            <span className="text-emerald-400 text-xs">✓ Valid range</span>
          )}
        </div>

        {/* 超时时间设置 */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">
            Timeout (seconds): {config.timeout_seconds}s
          </label>
          <input
            type="range"
            min="10"
            max="300"
            step="10"
            value={config.timeout_seconds}
            onChange={(e) => setConfig({ ...config, timeout_seconds: Number(e.target.value) })}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>10s</span>
            <span>300s</span>
          </div>
          {config.timeout_seconds < 10 || config.timeout_seconds > 300 ? (
            <span className="text-red-400 text-xs">⚠️ Must be between 10 and 300 seconds</span>
          ) : (
            <span className="text-emerald-400 text-xs">✓ Valid range</span>
          )}
        </div>

        {/* 最大并发容器数设置 */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">
            Max Concurrent Containers: {config.max_concurrent_containers}
          </label>
          <input
            type="range"
            min="1"
            max="10"
            step="1"
            value={config.max_concurrent_containers}
            onChange={(e) => setConfig({ ...config, max_concurrent_containers: Number(e.target.value) })}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>1</span>
            <span>10</span>
          </div>
          {config.max_concurrent_containers < 1 || config.max_concurrent_containers > 10 ? (
            <span className="text-red-400 text-xs">⚠️ Must be between 1 and 10</span>
          ) : (
            <span className="text-emerald-400 text-xs">✓ Valid range</span>
          )}
        </div>

        {/* 保存按钮 */}
        <button
          onClick={handleSave}
          disabled={loading}
          className="w-full py-2 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 rounded text-white font-medium transition-colors"
        >
          {loading ? 'Saving...' : 'Save Docker Configuration'}
        </button>
      </div>
    </div>
  );
};

export default DockerConfigPanel;
