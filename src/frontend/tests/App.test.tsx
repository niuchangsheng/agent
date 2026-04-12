import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import App from '../src/App';

// Mock fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch as any;

describe('App Root Render & Health Check', () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it('应当能够挂载并且存在 SECA Core Control 标题', () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'active' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });
    render(<App />);
    expect(screen.getByText(/SECA Core Control/i)).toBeInTheDocument();
  });

  it('应当能嗅探后端健康情况并展示连通状态 [Connected]', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'active' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/\[Connected\]/i)).toBeInTheDocument();
    });
  });

  it('当后端宕机离线时，界面应展示超时红灯断开的提示', async () => {
    mockFetch
      .mockRejectedValueOnce(new Error('Network response was not ok'))
      .mockRejectedValueOnce(new Error('Network response was not ok'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/\[Disconnected\]/i)).toBeInTheDocument();
    });
  });
});
