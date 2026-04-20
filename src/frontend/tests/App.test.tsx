import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../src/App';

// Mock fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch as any;

describe('App Root Render - Sprint 20 UX', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('应当能够挂载并显示 SingleInputView 默认界面', () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'active' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });
    render(<App />);
    // 新界面默认显示输入框
    expect(screen.getByPlaceholderText(/例如|修复|JWT/i)).toBeInTheDocument();
  });

  it('应当显示提交按钮和高级模式入口', () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'active' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });
    render(<App />);
    // 提交按钮存在
    expect(screen.getByRole('button', { name: /提交/i })).toBeInTheDocument();
    // 高级模式入口存在
    expect(screen.getByRole('button', { name: /高级/i })).toBeInTheDocument();
  });

  it('点击高级模式应显示 Dashboard 和连接状态', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'active' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<App />);

    // 点击高级模式按钮
    const advancedBtn = screen.getByRole('button', { name: /高级/i });
    fireEvent.click(advancedBtn);

    await waitFor(() => {
      // 高级模式显示 SECA Core Control 标题
      expect(screen.getByText(/SECA Core Control/i)).toBeInTheDocument();
      // 连接状态显示
      expect(screen.getByText(/\[Connected\]/i)).toBeInTheDocument();
    });
  });
});
