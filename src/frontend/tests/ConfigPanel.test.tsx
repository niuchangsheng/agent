import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import ConfigPanel from '../src/components/ConfigPanel';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('ConfigPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('应当渲染配置面板标题', () => {
    mockFetch
      .mockResolvedValueOnce({ json: () => Promise.resolve([]) }) // 项目列表
      .mockResolvedValueOnce({ json: () => Promise.resolve(null), status: 404 }); // 配置不存在

    render(<ConfigPanel projectId={1} />);

    expect(screen.getByText(/Configuration Center/)).toBeInTheDocument();
  });

  it('应当显示沙箱超时滑块', async () => {
    mockFetch
      .mockResolvedValueOnce({ json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ status: 404 });

    render(<ConfigPanel projectId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Sandbox Timeout/)).toBeInTheDocument();
    });
  });

  it('应当显示内存配额滑块', async () => {
    mockFetch
      .mockResolvedValueOnce({ json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ status: 404 });

    render(<ConfigPanel projectId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Max Memory/)).toBeInTheDocument();
    });
  });

  it('应当能添加环境变量', async () => {
    mockFetch
      .mockResolvedValueOnce({ json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ status: 404 });

    render(<ConfigPanel projectId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Add Variable/)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText(/Add Variable/));
    expect(screen.getByPlaceholderText('KEY')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('value')).toBeInTheDocument();
  });

  it('应当能保存配置', async () => {
    const mockConfig = {
      project_id: 1,
      sandbox_timeout_seconds: 45,
      max_memory_mb: 1024,
      environment_variables: { TEST_VAR: 'test_value' },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    mockFetch
      .mockResolvedValueOnce({ json: () => Promise.resolve([]) })
      .mockResolvedValueOnce({ status: 404, json: () => Promise.resolve({}) })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockConfig)
      });

    const { getByText, getByPlaceholderText, container } = render(<ConfigPanel projectId={1} />);

    await waitFor(() => {
      expect(getByText(/Configuration/)).toBeInTheDocument();
    });

    // 添加环境变量
    fireEvent.click(getByText(/Add Variable/));
    fireEvent.change(getByPlaceholderText('KEY'), { target: { value: 'TEST_VAR' } });
    fireEvent.change(getByPlaceholderText('value'), { target: { value: 'test_value' } });

    // 点击保存按钮 - 使用容器查找按钮
    const saveButton = container.querySelector('button[type="submit"]') || container.querySelectorAll('button')[container.querySelectorAll('button').length - 1];
    if (saveButton) {
      fireEvent.click(saveButton);
    }

    // 验证保存后显示成功消息
    await waitFor(() => {
      expect(getByText(/Configuration saved successfully/)).toBeInTheDocument();
    });

    // 验证 API 调用
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/projects/1/config',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
    );
  });
});
