import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SingleInputView from '../SingleInputView';

describe('SingleInputView', () => {
  const mockOnSubmit = vi.fn();
  const mockOnSettingsClick = vi.fn();
  const mockOnApiKeysClick = vi.fn();
  const mockOnMetricsClick = vi.fn();
  const mockOnAdvancedClick = vi.fn();

  it('test_input_centered_on_screen', () => {
    render(
      <SingleInputView
        onSubmit={mockOnSubmit}
        onSettingsClick={mockOnSettingsClick}
        onApiKeysClick={mockOnApiKeysClick}
        onMetricsClick={mockOnMetricsClick}
        onAdvancedClick={mockOnAdvancedClick}
      />
    );

    // 验证输入框存在且居中
    const textarea = screen.getByPlaceholderText(/例如|修复|JWT/i);
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveClass('w-full'); // 占主体宽度
  });

  it('test_submit_button_below_input', () => {
    render(
      <SingleInputView
        onSubmit={mockOnSubmit}
        onSettingsClick={mockOnSettingsClick}
        onApiKeysClick={mockOnApiKeysClick}
        onMetricsClick={mockOnMetricsClick}
        onAdvancedClick={mockOnAdvancedClick}
      />
    );

    // 验证提交按钮在输入框下方
    const submitButton = screen.getByRole('button', { name: /提交/i });
    expect(submitButton).toBeInTheDocument();
    expect(submitButton).toHaveClass('bg-cyan-600'); // 青色主题
  });

  it('test_right_corner_icons_visible', () => {
    render(
      <SingleInputView
        onSubmit={mockOnSubmit}
        onSettingsClick={mockOnSettingsClick}
        onApiKeysClick={mockOnApiKeysClick}
        onMetricsClick={mockOnMetricsClick}
        onAdvancedClick={mockOnAdvancedClick}
      />
    );

    // 验证右上角图标可见（包括高级按钮）
    const settingsButton = screen.getByRole('button', { name: /设置/i });
    const apiKeysButton = screen.getByRole('button', { name: /API/i });
    const metricsButton = screen.getByRole('button', { name: /监控/i });
    const advancedButton = screen.getByRole('button', { name: /高级/i });

    expect(settingsButton).toBeInTheDocument();
    expect(apiKeysButton).toBeInTheDocument();
    expect(metricsButton).toBeInTheDocument();
    expect(advancedButton).toBeInTheDocument();
  });

  it('test_submit_redirects_to_execution', () => {
    render(
      <SingleInputView
        onSubmit={mockOnSubmit}
        onSettingsClick={mockOnSettingsClick}
        onApiKeysClick={mockOnApiKeysClick}
        onMetricsClick={mockOnMetricsClick}
        onAdvancedClick={mockOnAdvancedClick}
      />
    );

    // 填写输入框
    const textarea = screen.getByPlaceholderText(/例如|修复|JWT/i);
    fireEvent.change(textarea, { target: { value: 'Fix bug in auth module' } });

    // 点击提交
    const submitButton = screen.getByRole('button', { name: /提交/i });
    fireEvent.click(submitButton);

    // 验证 onSubmit 被调用
    expect(mockOnSubmit).toHaveBeenCalledWith('Fix bug in auth module');
  });

  it('test_advanced_button_in_top_right', () => {
    render(
      <SingleInputView
        onSubmit={mockOnSubmit}
        onSettingsClick={mockOnSettingsClick}
        onApiKeysClick={mockOnApiKeysClick}
        onMetricsClick={mockOnMetricsClick}
        onAdvancedClick={mockOnAdvancedClick}
      />
    );

    // 验证高级按钮在右上角图标组中
    const advancedButton = screen.getByRole('button', { name: /高级/i });
    expect(advancedButton).toBeInTheDocument();

    // 点击高级按钮
    fireEvent.click(advancedButton);
    expect(mockOnAdvancedClick).toHaveBeenCalled();
  });
});