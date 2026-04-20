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

function LiveExecutionView({ taskId, onComplete, isCompleted = false }: LiveExecutionViewProps) {
  const [status, setStatus] = useState<string>(isCompleted ? 'COMPLETED' : 'RUNNING');
  const [output, setOutput] = useState<string[]>([]);
  const [loading, setLoading] = useState(!isCompleted);

  // 首先获取任务状态
  useEffect(() => {
    const fetchTaskStatus = async () => {
      try {
        const apiKey = localStorage.getItem('api_key') || '';
        const res = await fetch(`/api/v1/tasks/${taskId}`, {
          headers: {
            'X-API-Key': apiKey
          }
        });
        if (res.ok) {
          const task: TaskStatus = await res.json();
          setStatus(task.status);

          // 如果任务已完成，显示完成消息
          if (task.status === 'COMPLETED') {
            setOutput([
              `任务执行完成`,
              `状态: ${task.status_message}`,
              `进度: ${task.progress_percent}%`
            ]);
            setLoading(false);
          }
        }
      } catch (err) {
        console.warn('Failed to fetch task status:', err);
      }
    };

    if (!isCompleted) {
      fetchTaskStatus();
    }
  }, [taskId, isCompleted]);

  // SSE 连接（仅在任务运行中）
  useEffect(() => {
    if (isCompleted || status === 'COMPLETED') {
      return;
    }

    // SSE connection (仅在浏览器环境)
    if (typeof window !== 'undefined' && typeof EventSource !== 'undefined') {
      const eventSource = new EventSource(`/api/v1/tasks/${taskId}/stream`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLoading(false);
          if (data.type === 'status') {
            setStatus(data.content || 'RUNNING');
          } else if (data.type === 'perception' || data.type === 'reasoning' || data.type === 'action') {
            setOutput(prev => [...prev, data.content || data.message || '']);
          } else if (data.type === 'complete') {
            setStatus('COMPLETED');
            setOutput(prev => [...prev, '任务执行完成']);
          } else if (data.type === 'error') {
            setStatus('FAILED');
            setOutput(prev => [...prev, `错误: ${data.error || data.message || '未知错误'}`]);
          }
        } catch (e) {
          console.warn('Failed to parse SSE event:', e);
        }
      };

      eventSource.onerror = () => {
        setLoading(false);
        // 连接关闭时，再次检查任务状态
        const checkStatus = async () => {
          try {
            const apiKey = localStorage.getItem('api_key') || '';
            const res = await fetch(`/api/v1/tasks/${taskId}`, {
              headers: { 'X-API-Key': apiKey }
            });
            if (res.ok) {
              const task: TaskStatus = await res.json();
              if (task.status === 'COMPLETED') {
                setStatus('COMPLETED');
                setOutput(prev => [...prev, '任务执行完成']);
              }
            }
          } catch {}
        };
        checkStatus();
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    }
  }, [taskId, isCompleted, status]);

  const statusColor = status === 'COMPLETED' ? 'bg-emerald-500' : status === 'FAILED' ? 'bg-red-500' : 'bg-cyan-500';

  return (
    <div data-testid="live-execution-view" className="flex-1 min-h-screen bg-slate-950 text-slate-300 p-8 flex flex-col animate-view-transition">
      {/* 状态指示 */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <span data-testid="status-indicator" className={`px-3 py-1 ${statusColor} text-white text-sm rounded-full font-mono`}>
            {status}
          </span>
          <span className="text-slate-500 text-sm">Task #{taskId}</span>
        </div>

        {status === 'COMPLETED' && (
          <button
            onClick={onComplete}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            新任务
          </button>
        )}
      </div>

      {/* 流式输出区域 */}
      <div
        data-testid="streaming-output"
        className="flex-1 p-4 bg-slate-900/80 backdrop-blur-sm border border-slate-700 rounded-xl overflow-auto"
      >
        {loading && output.length === 0 ? (
          <div className="text-slate-500 text-center py-8 flex flex-col items-center gap-3">
            <svg className="w-8 h-8 animate-spin text-cyan-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span>等待 Agent 输出...</span>
          </div>
        ) : output.length === 0 ? (
          <div className="text-slate-500 text-center py-8">
            无输出记录
          </div>
        ) : (
          <div className="font-mono text-sm space-y-2">
            {output.map((line, idx) => (
              <div key={idx} className="text-slate-300">{line}</div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveExecutionView;