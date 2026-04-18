import { useEffect, useState } from 'react';

interface Project {
  id: number;
  name: string;
  target_repo_path: string;
}

interface Task {
  id: number;
  project_id: number;
  raw_objective: string;
  status: string;
}

interface TaskSubmitPanelProps {
  onTaskCreated?: (task: Task) => void;
}

const TaskSubmitPanel: React.FC<TaskSubmitPanelProps> = ({ onTaskCreated }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [objective, setObjective] = useState('');
  const [priority, setPriority] = useState(0);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [objectiveError, setObjectiveError] = useState<string | null>(null);

  const apiKey = localStorage.getItem('api_key') || '';
  const hasApiKey = apiKey.length > 0;

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/v1/projects', {
        headers: {
          'X-API-Key': apiKey,
        },
      });

      if (!res.ok) throw new Error('Failed to fetch projects');
      const data = await res.json();
      setProjects(data);

      // Auto-select first project if available
      if (data.length > 0) {
        setSelectedProjectId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch projects');
    } finally {
      setLoading(false);
    }
  };

  // Validate objective length
  const validateObjective = (value: string) => {
    setObjective(value);
    if (value.length > 500) {
      setObjectiveError('字数超限（最多500字）');
    } else {
      setObjectiveError(null);
    }
  };

  // Handle submit
  const handleSubmit = async () => {
    // Validate required fields
    if (!objective.trim()) {
      setError('请输入任务目标');
      return;
    }

    if (!selectedProjectId) {
      setError('请选择项目');
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
        },
        body: JSON.stringify({
          project_id: selectedProjectId,
          raw_objective: objective,
          priority: priority,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || '提交失败');
      }

      const task = await res.json();
      setSuccess('任务提交成功！');
      setObjective('');
      setPriority(0);
      onTaskCreated?.(task);

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : '提交失败');
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = hasApiKey && projects.length > 0 && !submitting;

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-900/20">
      <h2 className="text-xl mb-4 border-b border-slate-700 pb-2 text-white">
        📝 提交任务
      </h2>

      {/* API Key Warning */}
      {!hasApiKey && (
        <div className="mb-4 p-3 bg-orange-900/30 border border-orange-500/50 rounded text-orange-300 text-sm">
          ⚠️ 请先创建 API Key 才能提交任务
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="text-slate-500 animate-pulse">加载项目列表...</div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mb-4 p-3 bg-emerald-900/30 border border-emerald-500/50 rounded text-emerald-300 text-sm">
          {success}
        </div>
      )}

      {/* No Projects Warning */}
      {!loading && projects.length === 0 && hasApiKey && (
        <div className="mb-4 p-3 bg-yellow-900/30 border border-yellow-500/50 rounded text-yellow-300 text-sm">
          ⚠️ 请先创建项目才能提交任务
        </div>
      )}

      {/* Form */}
      {!loading && projects.length > 0 && (
        <div className="space-y-4">
          {/* Project Selector */}
          <div>
            <label className="block text-sm text-slate-400 mb-1">
              选择项目:
            </label>
            <select
              value={selectedProjectId || ''}
              onChange={(e) => setSelectedProjectId(Number(e.target.value))}
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-300 focus:border-cyan-500 focus:outline-none"
              disabled={!hasApiKey}
            >
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>

          {/* Objective Input */}
          <div>
            <label className="block text-sm text-slate-400 mb-1">
              任务目标:
            </label>
            <textarea
              value={objective}
              onChange={(e) => validateObjective(e.target.value)}
              placeholder="描述你的任务目标..."
              className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-300 focus:border-cyan-500 focus:outline-none min-h-[100px] resize-y"
              disabled={!hasApiKey}
            />
            <div className="flex justify-between text-xs mt-1">
              <span className={objectiveError ? 'text-red-400' : 'text-slate-500'}>
                {objectiveError || `${objective.length}/500`}
              </span>
            </div>
          </div>

          {/* Priority Selector */}
          <div>
            <label className="block text-sm text-slate-400 mb-1">
              优先级 (0-10):
            </label>
            <div className="flex items-center gap-2">
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={priority}
                onChange={(e) => setPriority(Number(e.target.value))}
                className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
                disabled={!hasApiKey}
              />
              <span className={`text-sm font-mono ${priority >= 7 ? 'text-red-400' : 'text-slate-400'}`}>
                {priority}
              </span>
              {priority >= 7 && (
                <span className="text-xs text-red-400">⚠️ 高优先级</span>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="w-full py-3 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg text-white font-medium transition-colors"
          >
            {submitting ? '提交中...' : '提交任务'}
          </button>
        </div>
      )}
    </div>
  );
};

export default TaskSubmitPanel;