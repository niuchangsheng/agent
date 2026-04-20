import { useState, useEffect } from 'react';

interface LiveExecutionViewProps {
  taskId: number;
  onComplete: () => void;
  isCompleted?: boolean;
}

interface TaskStatus {
  id: number;
  status: string;
  status_message: string;
  progress_percent: number;
}

interface TraceRecord {
  id: number;
  agent_role: string;
  perception_log: string;
  reasoning_log: string;
  applied_patch: string;
  is_success: boolean;
}

function LiveExecutionView({ taskId, onComplete, isCompleted = false }: LiveExecutionViewProps) {
  const [status, setStatus] = useState<string>(isCompleted ? 'COMPLETED' : 'RUNNING');
  const [output, setOutput] = useState<string[]>([]);
  const [loading, setLoading] = useState(!isCompleted);

  // 格式化事件内容
  const formatOutput = (type: string, data: any): string => {
    switch (type) {
      case 'perception':
        return `🧠 [感知] 目标: ${data.objective || ''}`;
      case 'decision':
        return `💭 [决策] ${data.action || ''} - ${data.reasoning || ''}`;
      case 'action':
        return `${data.success ? '✓' : '✕'} [执行] ${data.action_type || ''} ${data.summary || ''}`;
      case 'progress':
        return `📊 [进度] ${data.percent}%`;
      case 'complete':
        return `✅ [完成] 任务执行成功`;
      case 'error':
        return `❌ [错误] ${data.error || ''}`;
      case 'start':
        return `🚀 [启动] Worker: ${data.worker_id || ''}`;
      default:
        return `[${type}] ${JSON.stringify(data).slice(0, 80)}`;
    }
  };

  // 获取 Trace 历史
  const fetchTraceHistory = async () => {
    try {
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) return;

      const res = await fetch(`/api/v1/tasks/${taskId}/traces`, {
        headers: { 'X-API-Key': apiKey }
      });

      if (res.ok) {
        const traces: TraceRecord[] = await res.json();
        if (traces.length > 0) {
          const history: string[] = [];
          traces.forEach(t => {
            try {
              if (t.perception_log) {
                const p = JSON.parse(t.perception_log);
                history.push(formatOutput('perception', p));
              }
              if (t.reasoning_log) {
                const d = JSON.parse(t.reasoning_log);
                history.push(formatOutput('decision', d));
              }
              if (t.applied_patch) {
                const a = JSON.parse(t.applied_patch);
                history.push(formatOutput('action', a));
              }
            } catch {}
          });
          setOutput(history);
          setLoading(false);
        }
      }
    } catch (err) {
      console.warn('Failed to fetch traces:', err);
    }
  };

  // 初始化：检查任务状态
  useEffect(() => {
    const init = async () => {
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        setLoading(false);
        return;
      }

      try {
        const res = await fetch(`/api/v1/tasks/${taskId}`, {
          headers: { 'X-API-Key': apiKey }
        });
        if (res.ok) {
          const task: TaskStatus = await res.json();
          setStatus(task.status);
          if (task.status === 'COMPLETED' || task.status === 'FAILED') {
            await fetchTraceHistory();
          }
        }
      } catch (err) {
        console.warn('Failed to fetch task:', err);
        setLoading(false);
      }
    };

    init();
  }, [taskId]);

  // SSE 连接（仅运行中任务）
  useEffect(() => {
    if (status === 'COMPLETED' || status === 'FAILED') return;

    const eventSource = new EventSource(`/api/v1/tasks/${taskId}/stream`);

    // 处理不同事件类型
    const handleEvent = (type: string, data: any) => {
      setLoading(false);
      setOutput(prev => [...prev, formatOutput(type, data)]);
    };

    eventSource.addEventListener('connected', (e) => {
      console.log('SSE connected');
    });

    eventSource.addEventListener('perception', (e) => {
      try {
        handleEvent('perception', JSON.parse(e.data));
      } catch {}
    });

    eventSource.addEventListener('decision', (e) => {
      try {
        handleEvent('decision', JSON.parse(e.data));
      } catch {}
    });

    eventSource.addEventListener('action', (e) => {
      try {
        handleEvent('action', JSON.parse(e.data));
      } catch {}
    });

    eventSource.addEventListener('progress', (e) => {
      try {
        handleEvent('progress', JSON.parse(e.data));
      } catch {}
    });

    eventSource.addEventListener('complete', (e) => {
      setStatus('COMPLETED');
      handleEvent('complete', {});
      eventSource.close();
    });

    eventSource.addEventListener('error', (e) => {
      try {
        const data = JSON.parse(e.data);
        setStatus('FAILED');
        handleEvent('error', data);
      } catch {}
    });

    eventSource.addEventListener('heartbeat', () => {
      // 保持连接，不显示
    });

    eventSource.onerror = () => {
      setLoading(false);
      // 断开后检查任务状态
      fetchTraceHistory();
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [taskId, status]);

  const statusColor = status === 'COMPLETED' ? 'bg-emerald-500' : status === 'FAILED' ? 'bg-red-500' : 'bg-cyan-500 animate-pulse';

  return (
    <div data-testid="live-execution-view" className="min-h-screen bg-slate-950 text-slate-300 p-4 flex flex-col animate-view-transition">
      {/* 状态栏 */}
      <div className="flex justify-between items-center mb-4 px-4">
        <div className="flex items-center gap-3">
          <span data-testid="status-indicator" className={`px-3 py-1 rounded-full text-sm font-mono ${statusColor}`}>
            {status}
          </span>
          <span className="text-slate-500">Task #{taskId}</span>
        </div>

        {status === 'COMPLETED' && (
          <button onClick={onComplete} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新任务
          </button>
        )}
      </div>

      {/* 输出面板 */}
      <div data-testid="streaming-output" className="flex-1 mx-4 p-4 bg-slate-900/80 backdrop-blur border border-slate-700 rounded-xl overflow-auto">
        {loading && output.length === 0 ? (
          <div className="text-center py-8 text-slate-500">
            <svg className="w-8 h-8 mx-auto animate-spin text-cyan-400 mb-3" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Agent 正在思考...
          </div>
        ) : output.length === 0 ? (
          <div className="text-center py-8 text-slate-500">无执行记录</div>
        ) : (
          <div className="space-y-2 font-mono text-sm">
            {output.map((line, i) => (
              <div key={i} className={`px-3 py-2 rounded ${
                line.includes('✓') || line.includes('✅') ? 'bg-emerald-900/20' :
                line.includes('✕') || line.includes('❌') ? 'bg-red-900/20' :
                line.includes('🧠') ? 'bg-cyan-900/20' :
                line.includes('💭') ? 'bg-amber-900/20' :
                'bg-slate-800/30'
              }`}>
                {line}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveExecutionView;