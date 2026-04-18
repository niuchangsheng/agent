import { useEffect, useState } from 'react';

interface LogResponse {
  task_id: number;
  logs: string;
  total_lines: number;
  truncated: boolean;
}

interface DockerLogViewerProps {
  taskId: number;
}

type LogLevel = 'ALL' | 'INFO' | 'WARN' | 'ERROR';

const DockerLogViewer: React.FC<DockerLogViewerProps> = ({ taskId }) => {
  const [logData, setLogData] = useState<LogResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lines, setLines] = useState<number>(100);
  const [level, setLevel] = useState<LogLevel>('ALL');
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, [taskId, lines, level]);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);

    const apiKey = localStorage.getItem('api_key') || '';

    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/logs?lines=${lines}&level=${level}`, {
        headers: {
          'X-API-Key': apiKey
        }
      });

      if (!res.ok) throw new Error('Failed to fetch logs');
      const data = await res.json();
      setLogData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  };

  const getLevelColor = (line: string) => {
    if (line.includes('[ERROR]')) return 'text-red-400';
    if (line.includes('[WARN]')) return 'text-yellow-400';
    if (line.includes('[INFO]')) return 'text-emerald-400';
    return 'text-slate-300';
  };

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-purple-500/30 shadow-2xl shadow-purple-900/20">
      <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
        <h2 className="text-xl text-white flex items-center gap-2">
          <span>📜</span> Docker Log Viewer
          <span className="text-sm text-slate-500">Task #{taskId}</span>
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="px-3 py-1 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-700 rounded text-xs text-white"
          >
            {loading ? 'Loading...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* 控制栏 */}
      <div className="flex gap-4 mb-4 items-center flex-wrap">
        {/* 行数选择 */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Lines:</label>
          <select
            value={lines}
            onChange={(e) => setLines(Number(e.target.value))}
            className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-300 text-sm"
          >
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={500}>500</option>
            <option value={1000}>1000</option>
          </select>
        </div>

        {/* 级别筛选 */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Level:</label>
          <select
            value={level}
            onChange={(e) => setLevel(e.target.value as LogLevel)}
            className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-300 text-sm"
          >
            <option value="ALL">All</option>
            <option value="INFO">Info</option>
            <option value="WARN">Warn</option>
            <option value="ERROR">Error</option>
          </select>
        </div>

        {/* 自动滚动切换 */}
        <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="rounded bg-slate-800 border-slate-700"
          />
          Auto-scroll
        </label>

        {/* 总行数信息 */}
        {logData && (
          <span className="text-sm text-slate-500">
            Total: {logData.total_lines} lines
            {logData.truncated && ' (truncated)'}
          </span>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* 日志内容 */}
      <div
        className="bg-slate-950 rounded-lg border border-slate-800 p-4 font-mono text-sm max-h-96 overflow-y-auto"
        id="log-container"
      >
        {loading && !logData ? (
          <div className="text-slate-500 animate-pulse">Loading logs...</div>
        ) : logData?.logs ? (
          <pre className="whitespace-pre-wrap break-all">
            {logData.logs.split('\n').map((line, index) => (
              <div key={index} className={`${getLevelColor(line)} hover:bg-slate-900 px-1`}>
                {line || ' '}
              </div>
            ))}
          </pre>
        ) : (
          <div className="text-slate-500 text-center py-8">
            No logs available for this task
          </div>
        )}
      </div>
    </div>
  );
};

export default DockerLogViewer;
