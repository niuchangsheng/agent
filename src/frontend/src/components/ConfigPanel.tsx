import { useEffect, useState } from 'react';

interface ProjectConfig {
  project_id: number;
  sandbox_timeout_seconds: number;
  max_memory_mb: number;
  environment_variables: Record<string, string>;
}

interface Project {
  id: number;
  name: string;
}

interface ConfigPanelProps {
  projectId: number;
  onConfigChange?: (config: ProjectConfig) => void;
}

const ConfigPanel: React.FC<ConfigPanelProps> = ({ projectId, onConfigChange }) => {
  const [config, setConfig] = useState<ProjectConfig | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number>(projectId);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 环境变量编辑器状态
  const [envVars, setEnvVars] = useState<{ key: string; value: string }[]>([]);

  useEffect(() => {
    // 获取项目列表
    const apiKey = localStorage.getItem('api_key') || '';
    fetch('/api/v1/projects', {
      headers: {
        'X-API-Key': apiKey
      }
    })
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setProjects(data);
          if (data.length > 0 && !projectId) {
            setSelectedProjectId(data[0].id);
          }
        }
      })
      .catch(err => console.warn('Failed to fetch projects:', err));
  }, [projectId]);

  useEffect(() => {
    if (selectedProjectId) {
      fetchConfig(selectedProjectId);
    }
  }, [selectedProjectId]);

  const fetchConfig = async (projId: number) => {
    setLoading(true);
    setError(null);

    const apiKey = localStorage.getItem('api_key') || '';

    fetch(`/api/v1/projects/${projId}/config`, {
      headers: {
        'X-API-Key': apiKey
      }
    })
      .then(res => {
        if (res.status === 404) {
          setConfig(null);
          return null;
        }
        if (!res.ok) throw new Error('Failed to fetch config');
        return res.json();
      })
      .then(data => {
        if (data) {
          setConfig(data);
          // 初始化环境变量编辑器
          if (data.environment_variables) {
            setEnvVars(Object.entries(data.environment_variables).map(([key, value]) => ({ key, value })));
          }
        }
      })
      .catch(err => {
        if (err.message !== 'Failed to fetch config') {
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  };

  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    // 转换环境变量数组为对象
    const envVarsObj = envVars.reduce((acc, { key, value }) => {
      if (key.trim()) {
        acc[key.trim()] = value;
      }
      return acc;
    }, {} as Record<string, string>);

    const configData = {
      sandbox_timeout_seconds: config?.sandbox_timeout_seconds || 30,
      max_memory_mb: config?.max_memory_mb || 512,
      environment_variables: envVarsObj
    };

    const method = config ? 'PUT' : 'POST';
    const url = `/api/v1/projects/${selectedProjectId}/config`;

    try {
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configData)
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Failed to save config');
      }

      const savedConfig = await res.json();
      setConfig(savedConfig);
      setSuccess('Configuration saved successfully!');
      onConfigChange?.(savedConfig);

      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save config');
    } finally {
      setLoading(false);
    }
  };

  const addEnvVar = () => {
    setEnvVars([...envVars, { key: '', value: '' }]);
  };

  const removeEnvVar = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const updateEnvVar = (index: number, field: 'key' | 'value', value: string) => {
    const newEnvVars = [...envVars];
    newEnvVars[index] = { ...newEnvVars[index], [field]: value };
    setEnvVars(newEnvVars);
  };

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-purple-500/30 shadow-2xl shadow-purple-900/20">
      <h2 className="text-xl mb-4 border-b border-slate-700 pb-2 text-white flex justify-between">
        <span>⚙️ Configuration Center</span>
        {projects.length > 0 && (
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(Number(e.target.value))}
            className="px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-300 text-sm"
          >
            {projects.map(project => (
              <option key={project.id} value={project.id}>
                {project.name} (ID: {project.id})
              </option>
            ))}
          </select>
        )}
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
        {/* 沙箱超时设置 */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">
            Sandbox Timeout (seconds): {config?.sandbox_timeout_seconds || 30}s
          </label>
          <input
            type="range"
            min="1"
            max="60"
            value={config?.sandbox_timeout_seconds || 30}
            onChange={(e) => setConfig({ ...config!, sandbox_timeout_seconds: Number(e.target.value) })}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>1s</span>
            <span>60s</span>
          </div>
        </div>

        {/* 内存配额设置 */}
        <div>
          <label className="block text-sm text-slate-400 mb-1">
            Max Memory (MB): {config?.max_memory_mb || 512}MB
          </label>
          <input
            type="range"
            min="128"
            max="2048"
            step="128"
            value={config?.max_memory_mb || 512}
            onChange={(e) => setConfig({ ...config!, max_memory_mb: Number(e.target.value) })}
            className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>128MB</span>
            <span>2048MB</span>
          </div>
        </div>

        {/* 环境变量编辑器 */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-sm text-slate-400">Environment Variables</label>
            <button
              onClick={addEnvVar}
              className="px-2 py-1 bg-purple-600 hover:bg-purple-700 rounded text-xs text-white"
            >
              + Add Variable
            </button>
          </div>

          <div className="space-y-2">
            {envVars.map((envVar, index) => (
              <div key={index} className="flex gap-2 items-center">
                <input
                  type="text"
                  placeholder="KEY"
                  value={envVar.key}
                  onChange={(e) => updateEnvVar(index, 'key', e.target.value)}
                  className="flex-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-300 text-sm"
                />
                <input
                  type="text"
                  placeholder="value"
                  value={envVar.value}
                  onChange={(e) => updateEnvVar(index, 'value', e.target.value)}
                  className="flex-1 px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-300 text-sm"
                />
                <button
                  onClick={() => removeEnvVar(index)}
                  className="px-2 py-1 bg-red-600 hover:bg-red-700 rounded text-xs text-white"
                >
                  ×
                </button>
              </div>
            ))}
            {envVars.length === 0 && (
              <div className="text-slate-500 text-sm italic">No environment variables configured</div>
            )}
          </div>
        </div>

        {/* 保存按钮 */}
        <button
          onClick={handleSave}
          disabled={loading}
          className="w-full py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 rounded text-white font-medium transition-colors"
        >
          {loading ? 'Saving...' : config ? 'Update Configuration' : 'Create Configuration'}
        </button>
      </div>
    </div>
  );
};

export default ConfigPanel;
