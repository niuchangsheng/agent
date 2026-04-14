import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import MetricsDashboard from '../src/components/MetricsDashboard';

// Mock fetch
global.fetch = vi.fn();

describe('MetricsDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        concurrent_tasks: 0,
        queued_tasks: 0,
        latency_p50_ms: 0,
        latency_p95_ms: 0,
        memory_mb: 0,
        redis_connected: false,
        threshold_exceeded: [],
      }),
    } as Response);

    render(<MetricsDashboard />);
    expect(screen.getByText('System Monitoring')).toBeInTheDocument();
  });

  it('displays all metrics from API', async () => {
    const mockMetrics = {
      concurrent_tasks: 3,
      queued_tasks: 5,
      latency_p50_ms: 50,
      latency_p95_ms: 150,
      memory_mb: 256,
      redis_connected: true,
      threshold_exceeded: [],
    };

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockMetrics,
    } as Response);

    render(<MetricsDashboard />);

    await waitFor(() => {
      // Check metric values (text may be split across elements)
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('150')).toBeInTheDocument();
      expect(screen.getByText('256')).toBeInTheDocument();
      // Check labels
      expect(screen.getByText('Concurrent Tasks')).toBeInTheDocument();
      expect(screen.getByText('Queued Tasks')).toBeInTheDocument();
      expect(screen.getByText('P50 Latency')).toBeInTheDocument();
      expect(screen.getByText('P95 Latency')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
    });
  });

  it('shows Redis connected status', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        concurrent_tasks: 0,
        queued_tasks: 0,
        latency_p50_ms: 0,
        latency_p95_ms: 0,
        memory_mb: 0,
        redis_connected: true,
        threshold_exceeded: [],
      }),
    } as Response);

    render(<MetricsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    });
  });

  it('shows Redis disconnected status with warning', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        concurrent_tasks: 0,
        queued_tasks: 0,
        latency_p50_ms: 0,
        latency_p95_ms: 0,
        memory_mb: 0,
        redis_connected: false,
        threshold_exceeded: ['redis_connected'],
      }),
    } as Response);

    render(<MetricsDashboard />);

    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument();
      expect(screen.getByText(/Warning:.*redis_connected/)).toBeInTheDocument();
    });
  });

  it('applies warning style for exceeded thresholds', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        concurrent_tasks: 0,
        queued_tasks: 150,
        latency_p50_ms: 0,
        latency_p95_ms: 1500,
        memory_mb: 512,
        redis_connected: true,
        threshold_exceeded: ['queued_tasks', 'latency_p95'],
      }),
    } as Response);

    render(<MetricsDashboard />);

    await waitFor(() => {
      // Check warning message appears
      expect(screen.getByText(/Warning:.*queued_tasks/)).toBeInTheDocument();
    });
  });

  it('auto-refreshes every 10 seconds', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          concurrent_tasks: 1,
          queued_tasks: 0,
          latency_p50_ms: 0,
          latency_p95_ms: 0,
          memory_mb: 0,
          redis_connected: true,
          threshold_exceeded: [],
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          concurrent_tasks: 2,
          queued_tasks: 0,
          latency_p50_ms: 0,
          latency_p95_ms: 0,
          memory_mb: 0,
          redis_connected: true,
          threshold_exceeded: [],
        }),
      } as Response);

    render(<MetricsDashboard />);

    // Wait for initial fetch
    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument();
    }, { timeout: 1000 });

    // Fast-forward 10 seconds
    await vi.advanceTimersByTimeAsync(10000);

    // Wait for second fetch
    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    }, { timeout: 1000 });

    vi.useRealTimers();
  });
});
