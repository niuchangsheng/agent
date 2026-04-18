import { useEffect, useState } from 'react';

interface Container {
  container_id: string;
  task_id: number;
  task_objective: string;
  cpu_percent: number;
  memory_mb: number;
  network_rx_bytes: number;
  network_tx_bytes: number;
  running_time_seconds: number | null;
  alert: boolean;
}

interface ContainerMonitorProps {
  refreshInterval?: number;
}

const ContainerMonitor: React.FC<ContainerMonitorProps> = ({ refreshInterval = 5000 }) => {
  const [containers, setContainers] = useState<Container[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    fetchContainers();
    const interval = setInterval(fetchContainers, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const fetchContainers = async () => {
    setLoading(true);
    setError(null);

    const apiKey = localStorage.getItem('api_key') || '';

    try {
      const res = await fetch('/api/v1/containers', {
        headers: {
          'X-API-Key': apiKey
        }
      });

      if (!res.ok) throw new Error('Failed to fetch containers');
      const data = await res.json();
      setContainers(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch containers');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '-';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getCpuStatusClass = (cpuPercent: number) => {
    if (cpuPercent > 90) return 'text-red-400 bg-red-900/30';
    if (cpuPercent > 70) return 'text-orange-400 bg-orange-900/30';
    if (cpuPercent > 50) return 'text-yellow-400 bg-yellow-900/30';
    return 'text-emerald-400 bg-emerald-900/30';
  };

  const getMemoryStatusClass = (memoryMb: number) => {
    if (memoryMb > 400) return 'text-red-400 bg-red-900/30';
    if (memoryMb > 300) return 'text-orange-400 bg-orange-900/30';
    if (memoryMb > 200) return 'text-yellow-400 bg-yellow-900/30';
    return 'text-emerald-400 bg-emerald-900/30';
  };

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-900/20">
      <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
        <h2 className="text-xl text-white flex items-center gap-2">
          <span>📊</span> Container Resource Monitor
        </h2>
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-500">
            {lastUpdated ? `Updated: ${lastUpdated.toLocaleTimeString()}` : 'Never updated'}
          </span>
          <button
            onClick={fetchContainers}
            disabled={loading}
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-700 disabled:bg-slate-700 rounded text-xs text-white"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {containers.length === 0 ? (
        <div className="text-slate-500 text-center py-8">
          No running containers
        </div>
      ) : (
        <div className="space-y-3">
          {containers.map((container) => (
            <div
              key={container.container_id}
              className={`p-4 rounded-lg border ${container.alert ? 'border-red-500/50 bg-red-900/20' : 'border-slate-700 bg-slate-800/50'}`}
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-white font-medium">Container: {container.container_id}</h3>
                  <p className="text-slate-400 text-sm mt-1">
                    Task #{container.task_id}: {container.task_objective}
                  </p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-slate-500">Running Time</span>
                  <p className="text-white font-mono">{formatDuration(container.running_time_seconds)}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* CPU 使用率 */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">CPU</span>
                    <span className={getCpuStatusClass(container.cpu_percent)}>
                      {container.cpu_percent.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${container.cpu_percent > 90 ? 'bg-red-500' : container.cpu_percent > 70 ? 'bg-orange-500' : 'bg-cyan-500'}`}
                      style={{ width: `${Math.min(container.cpu_percent, 100)}%` }}
                    />
                  </div>
                </div>

                {/* 内存使用量 */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Memory</span>
                    <span className={getMemoryStatusClass(container.memory_mb)}>
                      {container.memory_mb.toFixed(0)} MB
                    </span>
                  </div>
                  <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all ${container.memory_mb > 400 ? 'bg-red-500' : container.memory_mb > 300 ? 'bg-orange-500' : 'bg-purple-500'}`}
                      style={{ width: `${Math.min((container.memory_mb / 512) * 100, 100)}%` }}
                    />
                  </div>
                </div>

                {/* 网络 IO */}
                <div>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">Network RX</span>
                    <span className="text-emerald-400">{formatBytes(container.network_rx_bytes)}</span>
                  </div>
                  <div className="flex justify-between text-xs mb-1 mt-2">
                    <span className="text-slate-400">Network TX</span>
                    <span className="text-cyan-400">{formatBytes(container.network_tx_bytes)}</span>
                  </div>
                </div>

                {/* 状态 */}
                <div className="text-right">
                  {container.alert ? (
                    <span className="px-2 py-1 bg-red-600 rounded text-xs text-white animate-pulse">
                      ⚠️ High CPU
                    </span>
                  ) : (
                    <span className="px-2 py-1 bg-emerald-600 rounded text-xs text-white">
                      ✓ Normal
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContainerMonitor;
