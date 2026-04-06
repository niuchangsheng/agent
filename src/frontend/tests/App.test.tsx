import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from '../src/App';
import * as React from 'react';

// Mock fetch for health detection
global.fetch = vi.fn() as any;

describe('App Root Render & Health Check', () => {
  it('应当能够挂载并且存在 SECA Control Panel 标题', () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'active' }),
    });
    render(<App />);
    expect(screen.getByText(/SECA Control Panel/i)).toBeInTheDocument();
  });

  it('应当能嗅探后端健康情况并展示连通状态 [Connected]', async () => {
    (global.fetch as any).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ status: 'active' }),
    });
    
    render(<App />);
    
    // 应该能够在请求后看到连通状态
    await waitFor(() => {
      expect(screen.getByText(/\[Connected\]/i)).toBeInTheDocument();
    });
  });

  it('当后端宕机离线时，界面应展示超时红灯断开的提示', async () => {
    (global.fetch as any).mockRejectedValueOnce(new Error('Network response was not ok'));
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText(/\[Disconnected\]/i)).toBeInTheDocument();
    });
  });
});
