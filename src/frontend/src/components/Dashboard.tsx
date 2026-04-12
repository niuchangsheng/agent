import { useEffect, useState } from 'react';

interface TraceEvent {
  type: string;
  content: string;
}

const Dashboard: React.FC<{ taskId: string }> = ({ taskId }) => {
  const [messages, setMessages] = useState<TraceEvent[]>([]);

  useEffect(() => {
    const sseUrl = `/api/v1/tasks/${taskId}/stream`;
    const eventSource = new EventSource(sseUrl);
    let messageReceived = false;

    eventSource.onmessage = (event) => {
      try {
        const parsed: TraceEvent = JSON.parse(event.data);
        setMessages(prev => [...prev, parsed]);
        messageReceived = true;
        // Close connection after receiving first message (backend sends static response)
        if (messageReceived) {
          eventSource.close();
        }
      } catch (e) {
        console.warn('Failed to parse SSE event:', e);
        eventSource.close();
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [taskId]);

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-900/20">
      <h2 className="text-xl mb-4 border-b border-slate-700 pb-2 text-white flex justify-between">
        <span>[SECA_LOGO] Introspection Dashboard</span>
        <span className="text-sm text-cyan-500">TaskID: {taskId}</span>
      </h2>

      <div className="h-96 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="text-slate-500 animate-pulse">Waiting for diagnostic trace data...</div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`p-2 rounded border-l-2 ${msg.type === 'status' ? 'border-cyan-400 bg-slate-800' : 'border-emerald-500 bg-emerald-950/30'} flex flex-col`}
            >
              <span className="text-xs text-slate-400 mb-1">▶ {msg.type.toUpperCase()}</span>
              <span className="text-sm">{msg.content}</span>
            </div>
          ))
        )}
        {/* Typewriter cursor effect */}
        <div className="inline-block w-2 h-4 bg-cyan-400 animate-pulse ml-1 mt-2"></div>
      </div>
    </div>
  );
};

export default Dashboard;
