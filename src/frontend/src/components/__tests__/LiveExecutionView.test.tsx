import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import LiveExecutionView from '../LiveExecutionView';

// Mock EventSource for SSE testing
class MockEventSource {
  url: string;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onopen: ((event: Event) => void) | null = null;
  readyState: number = 0;

  constructor(url: string) {
    this.url = url;
    // Simulate immediate connection
    setTimeout(() => {
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 0);
  }

  close() {
    this.readyState = 2;
  }

  addEventListener(type: string, callback: (event: Event) => void) {}
  removeEventListener(type: string, callback: (event: Event) => void) {}
}

describe('LiveExecutionView', () => {
  const mockOnComplete = vi.fn();
  const originalEventSource = global.EventSource;

  beforeEach(() => {
    global.EventSource = MockEventSource as unknown as typeof EventSource;
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.EventSource = originalEventSource;
  });

  it('test_streaming_output_display', async () => {
    await act(async () => {
      render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} />);
    });

    // 验证执行视图显示
    const executionView = screen.getByTestId('live-execution-view');
    expect(executionView).toBeInTheDocument();

    // 验证有输出区域
    const outputArea = screen.getByTestId('streaming-output');
    expect(outputArea).toBeInTheDocument();
  });

  it('test_status_indicator_visible', async () => {
    await act(async () => {
      render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} />);
    });

    // 验证状态指示显示
    const statusBadge = screen.getByTestId('status-indicator');
    expect(statusBadge).toBeInTheDocument();
  });

  it('test_new_task_button_after_completion', async () => {
    await act(async () => {
      render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} isCompleted={true} />);
    });

    // 任务完成后显示"新任务"按钮
    const newTaskButton = screen.getByRole('button', { name: /新任务/i });
    expect(newTaskButton).toBeInTheDocument();

    // 点击新任务按钮
    await act(async () => {
      fireEvent.click(newTaskButton);
    });
    expect(mockOnComplete).toHaveBeenCalled();
  });

  it('test_settings_panel_not_obscure_main', async () => {
    await act(async () => {
      render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} />);
    });

    // 验证执行视图使用 flex 布局
    const executionView = screen.getByTestId('live-execution-view');
    expect(executionView).toHaveClass('flex'); // 使用 flex 布局
  });
});