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
  created_at: string;
}

function LiveExecutionView({ taskId, onComplete, isCompleted = false }: LiveExecutionViewProps) {
  const [status, setStatus] = useState<string>(isCompleted ? 'COMPLETED' : 'RUNNING');
  const [output, setOutput] = useState<string[]>([]);
  const [loading, setLoading] = useState(!isCompleted);

  // 格式化事件内容为可读文本
  const formatEventContent = (eventType: string, data: any): string => {
    switch (eventType) {
      case 'perception':
        return `🧠 [感知] 目标: ${data.objective || ''} | 项目: ${data.project_path || ''}`;
      case 'decision':
        return `💭 [决策] ${data.action || ''} | 原因: ${data.reasoning || ''}`;
      case 'action':
        const successIcon = data.success ? '✓' : '✕';
        return `${successIcon} [执行] ${data.action_type || data.action || ''} | 结果: ${data.summary || data.result || ''}`;
      case 'progress':
        return `📊 [进度] ${data.percent}% | ${data.message || ''}`;
      case 'complete':
        return `✅ [完成] 任务执行成功`;
      case 'error':
        return `❌ [错误] ${data.error || data.message || ''}`;
      default:
        return `[${eventType}] ${JSON.stringify(data).slice(0, 100)}`;
    }
  };

  // 获取已完成任务的 Trace 记录
  const fetchTraceHistory = async () => {
    try {
      const apiKey = localStorage.getItem('api_key') || '';
      const res = await fetch(`/api/v1/tasks/${taskId}/traces`, {
        headers: { 'X-API-Key': apiKey }
      });
      if (res.ok) {
        const traces: TraceRecord[] = await res.json();
        if (traces.length > 0) {
          const historyOutput = traces.map(trace => {
            const perception = trace.perception_log ? JSON.parse(trace.perception_log) : {};
            const decision = trace.reasoning_log ? JSON.parse(trace.reasoning_log) : {};
            const action = trace.applied_patch ? JSON.parse(trace.applied_patch) : {};

            return [
              formatEventContent('perception', perception),
              formatEventContent('decision', decision),
              formatEventContent('action', action)
            ];
          }).flat();

          setOutput(historyOutput);
          setLoading(false);
        }
      }
    } catch (err) {
      console.warn('Failed to fetch trace history:', err);
    }
  };

  // 首先获取任务状态
  useEffect(() => {
    const fetchTaskStatus = async () => {
      try {
        const apiKey = localStorage.getItem('api_key') || '';
        const res = await fetch(`/api/v1/tasks/${taskId}`, {
          headers: { 'X-API-Key': apiKey }
        });
        if (res.ok) {
          const task: TaskStatus = await res.json();
          setStatus(task.status);

          // 如果任务已完成，获取 Trace 历史
          if (task.status === 'COMPLETED') {
            await fetchTraceHistory();
            setLoading(false);
          }
        }
      } catch (err) {
        console.warn('Failed to fetch task status:', err);
      }
    };

    fetchTaskStatus();
  }, [taskId, isCompleted]);

  // SSE 连接（仅在任务运行中）
  useEffect(() => {
    if (status === 'COMPLETED') {
      return;
    }

    // SSE connection (仅在浏览器环境)
    if (typeof window !== 'undefined' && typeof EventSource !== 'undefined') {
      const eventSource = new EventSource(`/api/v1/tasks/${taskId}/stream`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLoading(false);

          // 处理各种事件类型
          const eventType = data.type || event.type;
          const eventContent = formatEventContent(eventType, data);

          if (eventType === 'status') {
            setStatus(data.content || 'RUNNING');
          } else if (eventType !== 'heartbeat') {
            setOutput(prev => [...prev, eventContent]);
          }

          if (eventType === 'complete') {
            setStatus('COMPLETED');
          } else if (eventType === 'error') {
            setStatus('FAILED');
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
                // 获取 Trace 历史
                await fetchTraceHistory();
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
  }, [taskId, status]);

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
            <span>Agent 正在思考...</span>
          </div>
        ) : output.length === 0 ? (
          <div className="text-slate-500 text-center py-8">
            无执行记录
          </div>
        ) : (
          <div className="font-mono text-sm space-y-3">
            {output.map((line, idx) => (
              <div key={idx} className={`py-2 px-3 rounded ${
                line.includes('✓') || line.includes('✅') ? 'bg-emerald-900/20 border-l-2 border-emerald-500' :
                line.includes('✕') || line.includes('❌') ? 'bg-red-900/20 border-l-2 border-red-500' :
                line.includes('🧠') ? 'bg-cyan-900/20 border-l-2 border-cyan-500' :
                line.includes('💭') ? 'bg-amber-900/20 border-l-2 border-amber-500' :
                'bg-slate-800/30 border-l-2 border-slate-500'
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