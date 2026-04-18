import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ContainerMonitor from '../src/components/ContainerMonitor';

// Mock fetch
global.fetch = vi.fn();

describe('ContainerMonitor', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
    // Mock localStorage
    const mockLocalStorage = {
      getItem: vi.fn().mockReturnValue('test-api-key'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders empty state when no containers', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      expect(screen.getByText(/No running containers/i)).toBeInTheDocument();
    });
  });

  it('displays container stats from API', async () => {
    const mockContainers = [
      {
        container_id: 'abc123',
        task_id: 1,
        task_objective: 'Test task',
        cpu_percent: 45.5,
        memory_mb: 128,
        network_rx_bytes: 1024,
        network_tx_bytes: 512,
        running_time_seconds: 60,
        alert: false,
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockContainers,
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      expect(screen.getByText(/abc123/i)).toBeInTheDocument();
      expect(screen.getByText(/Test task/i)).toBeInTheDocument();
    });
  });

  it('shows CPU warning style for high usage', async () => {
    const mockContainers = [
      {
        container_id: 'abc123',
        task_id: 1,
        task_objective: 'Test task',
        cpu_percent: 95,
        memory_mb: 128,
        network_rx_bytes: 1024,
        network_tx_bytes: 512,
        running_time_seconds: 60,
        alert: true,
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockContainers,
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      expect(screen.getByText(/High CPU/i)).toBeInTheDocument();
    });
  });

  it('shows memory warning style for high usage', async () => {
    const mockContainers = [
      {
        container_id: 'abc123',
        task_id: 1,
        task_objective: 'Test task',
        cpu_percent: 45,
        memory_mb: 450,
        network_rx_bytes: 1024,
        network_tx_bytes: 512,
        running_time_seconds: 60,
        alert: false,
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockContainers,
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      expect(screen.getByText(/450 MB/i)).toBeInTheDocument();
    });
  });

  it('formats bytes correctly', async () => {
    const mockContainers = [
      {
        container_id: 'abc123',
        task_id: 1,
        task_objective: 'Test task',
        cpu_percent: 45,
        memory_mb: 128,
        network_rx_bytes: 1536, // 1.5 KB
        network_tx_bytes: 1048576, // 1 MB
        running_time_seconds: 60,
        alert: false,
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockContainers,
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      // Check Network RX and TX labels appear
      expect(screen.getByText(/Network RX/i)).toBeInTheDocument();
      expect(screen.getByText(/Network TX/i)).toBeInTheDocument();
    });
  });

  it('formats duration correctly', async () => {
    const mockContainers = [
      {
        container_id: 'abc123',
        task_id: 1,
        task_objective: 'Test task',
        cpu_percent: 45,
        memory_mb: 128,
        network_rx_bytes: 1024,
        network_tx_bytes: 512,
        running_time_seconds: 125, // 2:05
        alert: false,
      },
    ];

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockContainers,
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      expect(screen.getByText(/2:05/i)).toBeInTheDocument();
    });
  });

  it('auto-refreshes on interval', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      } as Response);

    render(<ContainerMonitor refreshInterval={5000} />);

    // Wait for initial fetch
    await waitFor(() => {
      expect(screen.getByText(/No running containers/i)).toBeInTheDocument();
    }, { timeout: 1000 });

    // Fast-forward 5 seconds
    await vi.advanceTimersByTimeAsync(5000);

    // Should have called fetch again
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 1000 });

    vi.useRealTimers();
  });

  it('handles missing API key gracefully', async () => {
    // Mock localStorage with no API key
    const mockLocalStorage = {
      getItem: vi.fn().mockReturnValue(''),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    render(<ContainerMonitor />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/containers',
        expect.objectContaining({
          headers: {
            'X-API-Key': ''
          }
        })
      );
    });
  });
});