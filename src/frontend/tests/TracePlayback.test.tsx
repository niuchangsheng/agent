import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TracePlayback from '../src/components/TracePlayback';

// Mock fetch
global.fetch = vi.fn();

describe('TracePlayback', () => {
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

  it('renders playback controls', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'Step 1', is_success: true, timestamp: '2026-04-19T00:00:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      // 播放控制按钮
      expect(screen.getByRole('button', { name: /播放/i })).toBeInTheDocument();
      // 倍速选择器
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  it('displays trace steps from API', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'Generating code', reasoning_log: 'Thinking...', is_success: true, timestamp: '2026-04-19T00:00:00' },
        { id: 2, agent_role: 'evaluator', perception_log: 'Evaluating result', is_success: true, timestamp: '2026-04-19T00:01:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      // 显示步骤数
      expect(screen.getByText(/步骤 1 \/ 2/i)).toBeInTheDocument();
      // 显示 perception_log 内容
      expect(screen.getByText(/Generating code/i)).toBeInTheDocument();
    });
  });

  it('play_pause_toggle_works', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'Step 1', is_success: true, timestamp: '2026-04-19T00:00:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /播放/i })).toBeInTheDocument();
    });

    // 点击播放
    const playButton = screen.getByRole('button', { name: /播放/i });
    fireEvent.click(playButton);

    await waitFor(() => {
      // 播放后按钮应变为暂停
      expect(screen.getByRole('button', { name: /暂停/i })).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it('speed_selector_changes_speed', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'Step 1', is_success: true, timestamp: '2026-04-19T00:00:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    // 选择 2x 倍速
    const speedSelect = screen.getByRole('combobox');
    fireEvent.change(speedSelect, { target: { value: '2' } });

    // 验证选择器值已更新
    expect(speedSelect.value).toBe('2');
  });

  it('timeline_slider_navigation', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'Step One', is_success: true, timestamp: '2026-04-19T00:00:00' },
        { id: 2, agent_role: 'evaluator', perception_log: 'Step Two', is_success: true, timestamp: '2026-04-19T00:01:00' },
        { id: 3, agent_role: 'generator', perception_log: 'Step Three', is_success: true, timestamp: '2026-04-19T00:02:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      expect(screen.getByRole('slider')).toBeInTheDocument();
    });

    // 滑动到步骤 2 (index 1)
    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '1' } });

    await waitFor(() => {
      // 验证步骤显示更新
      expect(screen.getByText(/步骤 2/i)).toBeInTheDocument();
    });
  });

  it('current_step_highlighted', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'First perception', is_success: true, timestamp: '2026-04-19T00:00:00' },
        { id: 2, agent_role: 'evaluator', perception_log: 'Second perception', is_success: true, timestamp: '2026-04-19T00:01:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      // 默认显示第一个 trace 的 perception_log
      expect(screen.getByText(/First perception/i)).toBeInTheDocument();
    });
  });

  it('handles empty_trace', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/暂无 Trace/i)).toBeInTheDocument();
    });
  });

  it('sends API key in headers', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, agent_role: 'generator', perception_log: 'Step 1', is_success: true, timestamp: '2026-04-19T00:00:00' },
      ],
    } as Response);

    render(<TracePlayback taskId={1} />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/tasks/1/traces',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-API-Key': 'test-api-key',
          }),
        })
      );
    });
  });
});