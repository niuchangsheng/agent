import { useEffect, useState } from 'react';

interface QueueTask {
  task_id: number;
  project_id: number;
  raw_objective: string;
  queued_at: string;
  position?: number;
}

interface RunningTask {
  task_id: number;
  worker_id: string;
  progress_percent: number;
  status_message: string;
  started_at: string;
}

interface QueueStatus {
  queued: QueueTask[];
  running: RunningTask[];
  max_concurrent: number;
  available_slots: number;
}

const TaskQueueDashboard: React.FC = () => {
  const [queueStatus, setQueueStatus] = useState<QueueStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchQueueStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/tasks/queue');
      if (!res.ok) throw new Error('Failed to fetch queue status');
      const data = await res.json();
      setQueueStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueStatus();
    // Poll every 2 seconds for real-time updates
    const interval = setInterval(fetchQueueStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleCancelTask = async (taskId: number) => {
    if (!confirm(`Cancel task #${taskId}?`)) return;

    try {
      const res = await fetch(`/api/v1/tasks/queue/${taskId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Failed to cancel task');
      await fetchQueueStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to cancel task');
    }
  };

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-amber-500/30 shadow-2xl shadow-amber-900/20">
      <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
        <h2 className="text-xl text-white">📋 Task Queue Dashboard</h2>
        <button
          onClick={fetchQueueStatus}
          className="px-3 py-1 bg-amber-600 hover:bg-amber-700 rounded text-sm text-white"
        >
          🔄 Refresh
        </button>
      </div>

      {loading && !queueStatus && (
        <div className="text-slate-500 animate-pulse">Loading queue status...</div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {queueStatus && (
        <>
          {/* 队列概览 */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="text-2xl font-bold text-amber-400">{queueStatus.queued.length}</div>
              <div className="text-sm text-slate-400">Queued</div>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="text-2xl font-bold text-emerald-400">{queueStatus.running.length}</div>
              <div className="text-sm text-slate-400">Running</div>
            </div>
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="text-2xl font-bold text-cyan-400">{queueStatus.available_slots}</div>
              <div className="text-sm text-slate-400">Available Slots</div>
            </div>
          </div>

          {/* 运行中任务 */}
          <div className="mb-6">
            <h3 className="text-lg text-emerald-400 mb-2 flex items-center gap-2">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
              Running Tasks ({queueStatus.running.length})
            </h3>
            <div className="space-y-2">
              {queueStatus.running.length === 0 ? (
                <div className="text-slate-500 italic">No running tasks</div>
              ) : (
                queueStatus.running.map(task => (
                  <div
                    key={task.task_id}
                    className="p-3 bg-slate-800/50 rounded border border-emerald-500/30"
                  >
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-white font-mono">Task #{task.task_id}</span>
                      <span className="text-xs text-slate-400">Worker: {task.worker_id}</span>
                    </div>
                    <div className="text-sm text-slate-300 mb-2">{task.raw_objective || task.status_message}</div>
                    {/* 进度条 */}
                    <div className="w-full h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 transition-all duration-300"
                        style={{ width: `${task.progress_percent}%` }}
                      />
                    </div>
                    <div className="text-xs text-slate-400 mt-1">{task.progress_percent}% complete</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 队列中任务 */}
          <div>
            <h3 className="text-lg text-amber-400 mb-2">Queued Tasks ({queueStatus.queued.length})</h3>
            <div className="space-y-2">
              {queueStatus.queued.length === 0 ? (
                <div className="text-slate-500 italic">Queue is empty</div>
              ) : (
                queueStatus.queued.map(task => (
                  <div
                    key={task.task_id}
                    className="p-3 bg-slate-800/30 rounded border border-amber-500/20 flex justify-between items-center"
                  >
                    <div>
                      <div className="text-white font-mono">
                        Task #{task.task_id}
                        <span className="ml-2 px-2 py-0.5 bg-amber-600/30 text-amber-400 rounded text-xs">
                          Position #{task.position}
                        </span>
                      </div>
                      <div className="text-sm text-slate-400">{task.raw_objective}</div>
                    </div>
                    <button
                      onClick={() => handleCancelTask(task.task_id)}
                      className="px-3 py-1 bg-red-600/50 hover:bg-red-600 rounded text-xs text-white"
                    >
                      Cancel
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TaskQueueDashboard;
