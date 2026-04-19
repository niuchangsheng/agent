/**
 * useTaskStream - SSE 实时事件流 Hook
 *
 * 职责:
 * 1. 连接 SSE 端点
 * 2. 接收实时事件
 * 3. 处理连接状态
 */
import { useEffect, useState, useRef } from 'react';

interface SSEEvent {
  type: string;
  data: any;
  timestamp: string;
}

interface UseTaskStreamResult {
  events: SSEEvent[];
  isConnected: boolean;
  error: string | null;
  latestEvent: SSEEvent | null;
}

export function useTaskStream(taskId: number | null): UseTaskStreamResult {
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (!taskId) {
      return;
    }

    // 清理之前的连接
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    // 创建新连接
    const eventSource = new EventSource(`/api/v1/tasks/${taskId}/stream`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log(`SSE connected for task ${taskId}`);
    };

    eventSource.onerror = (e) => {
      setIsConnected(false);
      setError('Connection error');
      console.error('SSE error:', e);
    };

    // 监听连接事件
    eventSource.addEventListener('connected', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'connected',
        data,
        timestamp: new Date().toISOString()
      }]);
    });

    // 监听 start 事件
    eventSource.addEventListener('start', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'start',
        data,
        timestamp: new Date().toISOString()
      }]);
    });

    // 监听 perception 事件
    eventSource.addEventListener('perception', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'perception',
        data,
        timestamp: new Date().toISOString()
      }]);
    });

    // 监听 decision 事件
    eventSource.addEventListener('decision', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'decision',
        data,
        timestamp: new Date().toISOString()
      }]);
    });

    // 监听 action 事件
    eventSource.addEventListener('action', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'action',
        data,
        timestamp: new Date().toISOString()
      }]);
    });

    // 监听 progress 事件
    eventSource.addEventListener('progress', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'progress',
        data,
        timestamp: new Date().toISOString()
      }]);
    });

    // 监听 complete 事件
    eventSource.addEventListener('complete', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      setEvents(prev => [...prev, {
        type: 'complete',
        data,
        timestamp: new Date().toISOString()
      }]);
      // 完成后关闭连接
      eventSource.close();
      setIsConnected(false);
    });

    // 监听 error 事件
    eventSource.addEventListener('error', (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data);
        setEvents(prev => [...prev, {
          type: 'error',
          data,
          timestamp: new Date().toISOString()
        }]);
      } catch {
        // 解析失败，跳过
      }
    });

    // 监听心跳事件
    eventSource.addEventListener('heartbeat', (e: MessageEvent) => {
      // 心跳事件不添加到列表，仅保持连接活跃
    });

    return () => {
      eventSource.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    };
  }, [taskId]);

  // 获取最新事件
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  return {
    events,
    isConnected,
    error,
    latestEvent
  };
}

export default useTaskStream;