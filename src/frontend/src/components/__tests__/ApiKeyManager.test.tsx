import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ApiKeyManager from '../ApiKeyManager';

// Mock fetch
global.fetch = vi.fn();

const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe('ApiKeyManager', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders API Key manager component', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] }) // API Keys
      .mockResolvedValueOnce({ ok: true, json: async () => [] }); // Audit Logs

    render(<ApiKeyManager />);

    await waitFor(() => {
      expect(screen.getByText('创建 API Key')).toBeInTheDocument();
      expect(screen.getByText('API Key 列表')).toBeInTheDocument();
      expect(screen.getByText('审计日志')).toBeInTheDocument();
    });
  });

  it('shows empty state for API keys', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<ApiKeyManager />);

    await waitFor(() => {
      expect(screen.getByText('暂无 API Key')).toBeInTheDocument();
    });
  });

  it('shows empty state for audit logs', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<ApiKeyManager />);

    await waitFor(() => {
      expect(screen.getByText('暂无审计日志')).toBeInTheDocument();
    });
  });

  it('displays API key creation form', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<ApiKeyManager />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('例如：Deployment-Key')).toBeInTheDocument();
      expect(screen.getByText('生成 API Key')).toBeInTheDocument();
    });
  });

  it('displays permission checkboxes', async () => {
    mockFetch
      .mockResolvedValueOnce({ ok: true, json: async () => [] })
      .mockResolvedValueOnce({ ok: true, json: async () => [] });

    render(<ApiKeyManager />);

    await waitFor(() => {
      expect(screen.getByText('读取 (Read)')).toBeInTheDocument();
      expect(screen.getByText('写入 (Write)')).toBeInTheDocument();
      expect(screen.getByText('管理员 (Admin)')).toBeInTheDocument();
    });
  });
});
