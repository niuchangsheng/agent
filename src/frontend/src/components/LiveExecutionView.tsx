import { useState, useEffect } from 'react';

interface LiveExecutionViewProps {
  taskId: number;
  onComplete: () => void;
  isCompleted?: boolean;
}

function LiveExecutionView({ taskId, onComplete, isCompleted = false }: LiveExecutionViewProps) {
  const [status, setStatus] = useState<string>(isCompleted ? 'COMPLETED' : 'RUNNING');
  const [output, setOutput] = useState<string[]>([]);

  useEffect(() => {
    if (isCompleted) {
      setStatus('COMPLETED');
      return;
    }

    // SSE connection (仅在浏览器环境)
    if (typeof window !== 'undefined' && typeof EventSource !== 'undefined') {
      const eventSource = new EventSource(`/api/v1/tasks/${taskId}/stream`);

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'status') {
          setStatus(data.content || 'RUNNING');
        } else if (data.type === 'perception' || data.type === 'reasoning') {
          setOutput(prev => [...prev, data.content]);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
      };

      return () => {
        eventSource.close();
      };
    }
  }, [taskId, isCompleted]);

  const statusColor = status === 'COMPLETED' ? 'bg-emerald-500' : status === 'FAILED' ? 'bg-red-500' : 'bg-cyan-500';

  return (
    <div data-testid="live-execution-view" className="flex-1 min-h-screen bg-slate-950 text-slate-300 p-8 flex flex-col">
      {/* 状态指示 */}
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center gap-2">
          <span data-testid="status-indicator" className={`px-3 py-1 ${statusColor} text-white text-sm rounded-full font-mono`}>
            {status}
          </span>
          <span className="text-slate-500 text-sm">Task #{taskId}</span>
        </div>

        {isCompleted && (
          <button
            onClick={onComplete}
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl"
          >
            新任务
          </button>
        )}
      </div>

      {/* 流式输出区域 */}
      <div
        data-testid="streaming-output"
        className="flex-1 p-4 bg-slate-900/80 backdrop-blur-sm border border-slate-700 rounded-xl overflow-auto"
      >
        {output.length === 0 ? (
          <div className="text-slate-500 text-center py-8">
            等待 Agent 输出...
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