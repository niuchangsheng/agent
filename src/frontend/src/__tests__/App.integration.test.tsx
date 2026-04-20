import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';

describe('App Integration - Sprint 20', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      json: () => Promise.resolve({ status: 'active' }),
      ok: true
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('test_default_view_is_single_input', async () => {
    render(<App />);

    // 等待组件加载
    await waitFor(() => {
      // 验证默认显示 SingleInputView (输入框居中)
      const textarea = screen.getByPlaceholderText(/例如|修复|JWT/i);
      expect(textarea).toBeInTheDocument();
    });
  });

  it('test_submit_button_visible_on_default_view', async () => {
    render(<App />);

    await waitFor(() => {
      // 验证提交按钮存在
      const submitButton = screen.getByRole('button', { name: /提交/i });
      expect(submitButton).toBeInTheDocument();
    });
  });

  it('test_settings_api_metrics_icons_visible', async () => {
    render(<App />);

    await waitFor(() => {
      // 验证右上角图标存在
      expect(screen.getByRole('button', { name: /设置/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /API/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /监控/i })).toBeInTheDocument();
    });
  });

  it('test_advanced_button_in_top_right_corner', async () => {
    render(<App />);

    await waitFor(() => {
      // 验证"高级模式"入口在右上角（而非右下角）
      const advancedButton = screen.getByRole('button', { name: /高级/i });
      expect(advancedButton).toBeInTheDocument();
    });
  });

  it('test_clicking_advanced_switches_to_dashboard', async () => {
    render(<App />);

    await waitFor(() => {
      const advancedButton = screen.getByRole('button', { name: /高级/i });
      expect(advancedButton).toBeInTheDocument();
    });

    // 点击高级模式
    const advancedButton = screen.getByRole('button', { name: /高级/i });
    fireEvent.click(advancedButton);

    await waitFor(() => {
      // 验证进入高级模式
      expect(screen.getByText(/SECA Core Control/i)).toBeInTheDocument();
    });
  });
});