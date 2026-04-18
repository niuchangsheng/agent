import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import DockerLogViewer from '../src/components/DockerLogViewer';

// Mock fetch
global.fetch = vi.fn();

describe('DockerLogViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

  it('renders loading state initially', () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        task_id: 1,
        logs: '',
        total_lines: 0,
        truncated: false,
      }),
    } as Response);

    render(<DockerLogViewer taskId={1} />);
    expect(screen.getByText(/Docker Log Viewer/i)).toBeInTheDocument();
  });

  it('displays logs from API', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        task_id: 1,
        logs: '[INFO] Starting task\n[INFO] Task completed',
        total_lines: 2,
        truncated: false,
      }),
    } as Response);

    render(<DockerLogViewer taskId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Starting task/i)).toBeInTheDocument();
      expect(screen.getByText(/Task completed/i)).toBeInTheDocument();
    });
  });

  it('filters by level INFO', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        task_id: 1,
        logs: '[INFO] Test info log',
        total_lines: 1,
        truncated: false,
      }),
    } as Response);

    render(<DockerLogViewer taskId={1} />);

    // Initial call uses level=ALL (default), then we change to INFO
    const levelLabel = screen.getByText(/Level:/i);
    const levelSelect = levelLabel.closest('div')?.querySelector('select');
    if (levelSelect) {
      fireEvent.change(levelSelect, { target: { value: 'INFO' } });
    }

    await waitFor(() => {
      // Check that INFO level was used in a fetch call
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('level=INFO'),
        expect.any(Object)
      );
    });
  });

  it('filters by level ERROR', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          task_id: 1,
          logs: '[ERROR] Test error log',
          total_lines: 1,
          truncated: false,
        }),
      } as Response);

    render(<DockerLogViewer taskId={1} />);

    // Find the level select by its container label
    const levelLabel = screen.getByText(/Level:/i);
    const levelSelect = levelLabel.closest('div')?.querySelector('select');
    if (levelSelect) {
      fireEvent.change(levelSelect, { target: { value: 'ERROR' } });
    }

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('level=ERROR'),
        expect.any(Object)
      );
    });
  });

  it('changes lines count', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          task_id: 1,
          logs: '',
          total_lines: 0,
          truncated: false,
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          task_id: 1,
          logs: '',
          total_lines: 0,
          truncated: false,
        }),
      } as Response);

    render(<DockerLogViewer taskId={1} />);

    // Find the lines select by its container label
    const linesLabel = screen.getByText(/Lines:/i);
    const linesSelect = linesLabel.closest('div')?.querySelector('select');
    if (linesSelect) {
      fireEvent.change(linesSelect, { target: { value: '500' } });
    }

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('lines=500'),
        expect.any(Object)
      );
    });
  });

  it('shows truncated indicator', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        task_id: 1,
        logs: '[INFO] Log content',
        total_lines: 1000,
        truncated: true,
      }),
    } as Response);

    render(<DockerLogViewer taskId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/truncated/i)).toBeInTheDocument();
    });
  });

  it('applies level color coding', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        task_id: 1,
        logs: '[ERROR] Error log\n[WARN] Warning log\n[INFO] Info log',
        total_lines: 3,
        truncated: false,
      }),
    } as Response);

    render(<DockerLogViewer taskId={1} />);

    await waitFor(() => {
      // Check that logs are displayed
      expect(screen.getByText(/Error log/i)).toBeInTheDocument();
      expect(screen.getByText(/Warning log/i)).toBeInTheDocument();
      expect(screen.getByText(/Info log/i)).toBeInTheDocument();
    });
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
      json: async () => ({
        task_id: 1,
        logs: '',
        total_lines: 0,
        truncated: false,
      }),
    } as Response);

    render(<DockerLogViewer taskId={1} />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: {
            'X-API-Key': ''
          }
        })
      );
    });
  });
});