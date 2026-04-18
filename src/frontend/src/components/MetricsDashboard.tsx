import { useEffect, useState } from 'react';

interface MetricsData {
  concurrent_tasks: number;
  queued_tasks: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  memory_mb: number;
  redis_connected: boolean;
  queue_type: string;
  threshold_exceeded: string[];
}

const THRESHOLDS: Record<string, number> = {
  queued_tasks: 100,
  latency_p95_ms: 1000,
  memory_mb: 1024,
};

const MetricsCard: React.FC<{
  title: string;
  value: string | number;
  unit?: string;
  isWarning?: boolean;
}> = ({ title, value, unit = '', isWarning = false }) => (
  <div
    className={`p-4 rounded-lg border backdrop-blur-md ${
      isWarning
        ? 'bg-orange-900/30 border-orange-500/50 warning'
        : 'bg-slate-800/50 border-slate-600/50'
    }`}
  >
    <h3 className="text-sm text-slate-400 mb-2">{title}</h3>
    <p className={`text-2xl font-mono ${isWarning ? 'text-orange-400' : 'text-cyan-400'}`}>
      {value}
      {unit && <span className="text-sm ml-1 text-slate-500">{unit}</span>}
    </p>
  </div>
);

const MetricsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMetrics = async () => {
    try {
      // Get API key from localStorage
      const apiKey = localStorage.getItem('api_key') || '';
      const response = await fetch('/api/v1/metrics', {
        headers: {
          'X-API-Key': apiKey
        }
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: MetricsData = await response.json();
      setMetrics(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();

    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchMetrics, 10000);

    return () => clearInterval(interval);
  }, []);

  const isThresholdExceeded = (key: string) => {
    return metrics?.threshold_exceeded.includes(key) ?? false;
  };

  if (loading) {
    return (
      <div className="p-6 rounded-xl border border-slate-600/50 backdrop-blur-md bg-slate-800/30">
        <h2 className="text-xl mb-4 text-white">System Monitoring</h2>
        <div className="text-slate-500 animate-pulse">Loading metrics...</div>
      </div>
    );
  }

  if (error) {
    const needsApiKey = error.includes('401') || error.includes('API key');
    return (
      <div className="p-6 rounded-xl border border-red-500/50 backdrop-blur-md bg-red-900/30">
        <h2 className="text-xl mb-4 text-white">System Monitoring</h2>
        <div className="text-red-400">
          {needsApiKey ? (
            <div>
              <p className="mb-2">⚠️ API Key required. Please create an API key first.</p>
              <p className="text-sm text-slate-400">Go to the "API Keys" section to generate a key, then come back here.</p>
            </div>
          ) : (
            <>Error: {error}</>
          )}
        </div>
      </div>
    );
  }

  if (!metrics) {
    return null;
  }

  return (
    <div className="p-6 rounded-xl border border-cyan-500/30 backdrop-blur-md bg-slate-800/30 shadow-2xl shadow-cyan-900/20">
      <h2 className="text-xl mb-4 text-white flex justify-between items-center">
        <span>System Monitoring</span>
        <span className="text-xs text-slate-500">Auto-refresh: 10s</span>
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
        <MetricsCard
          title="Concurrent Tasks"
          value={metrics.concurrent_tasks}
          isWarning={isThresholdExceeded('concurrent_tasks')}
        />
        <MetricsCard
          title="Queued Tasks"
          value={metrics.queued_tasks}
          isWarning={isThresholdExceeded('queued_tasks')}
        />
        <MetricsCard
          title="P50 Latency"
          value={metrics.latency_p50_ms}
          unit="ms"
          isWarning={isThresholdExceeded('latency_p50')}
        />
        <MetricsCard
          title="P95 Latency"
          value={metrics.latency_p95_ms}
          unit="ms"
          isWarning={isThresholdExceeded('latency_p95')}
        />
        <MetricsCard
          title="Memory"
          value={Math.round(metrics.memory_mb)}
          unit="MB"
          isWarning={isThresholdExceeded('memory_mb')}
        />
        <MetricsCard
          title="Queue"
          value={
            metrics.queue_type === 'redis'
              ? (metrics.redis_connected ? 'Redis Connected' : 'Redis Disconnected')
              : metrics.queue_type === 'memory'
                ? 'Memory Queue'
                : 'Unknown'
          }
          isWarning={metrics.queue_type === 'redis' && !metrics.redis_connected}
        />
      </div>

      {metrics.threshold_exceeded.length > 0 && (
        <div className="p-3 rounded bg-orange-900/30 border border-orange-500/50">
          <p className="text-orange-400 text-sm">
            ⚠️ Warning: {metrics.threshold_exceeded.join(', ')} exceeded threshold
          </p>
        </div>
      )}
    </div>
  );
};

export default MetricsDashboard;
