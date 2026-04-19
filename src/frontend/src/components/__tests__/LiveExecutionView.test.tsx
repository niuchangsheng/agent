import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import LiveExecutionView from '../LiveExecutionView';

describe('LiveExecutionView', () => {
  const mockOnComplete = vi.fn();

  it('test_streaming_output_display', () => {
    render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} />);

    // 验证执行视图显示
    const executionView = screen.getByTestId('live-execution-view');
    expect(executionView).toBeInTheDocument();

    // 验证有输出区域
    const outputArea = screen.getByTestId('streaming-output');
    expect(outputArea).toBeInTheDocument();
  });

  it('test_status_indicator_visible', () => {
    render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} />);

    // 验证状态指示显示
    const statusBadge = screen.getByTestId('status-indicator');
    expect(statusBadge).toBeInTheDocument();
  });

  it('test_new_task_button_after_completion', () => {
    render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} isCompleted={true} />);

    // 任务完成后显示"新任务"按钮
    const newTaskButton = screen.getByRole('button', { name: /新任务/i });
    expect(newTaskButton).toBeInTheDocument();

    // 点击新任务按钮
    fireEvent.click(newTaskButton);
    expect(mockOnComplete).toHaveBeenCalled();
  });

  it('test_settings_panel_not_obscure_main', () => {
    render(<LiveExecutionView taskId={1} onComplete={mockOnComplete} />);

    // 验证执行视图占主体宽度
    const executionView = screen.getByTestId('live-execution-view');
    expect(executionView).toHaveClass('flex-1'); // 占据剩余空间
  });
});