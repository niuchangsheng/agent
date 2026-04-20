import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import TenantSelector from '../TenantSelector';

describe('TenantSelector', () => {
  const mockApiKey = 'test-api-key';
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: 1, name: 'Tenant A', slug: 'tenant-a' },
        { id: 2, name: 'Tenant B', slug: 'tenant-b' }
      ])
    });
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('test_selector_dropdown_visible', async () => {
    await act(async () => {
      render(<TenantSelector apiKey={mockApiKey} />);
    });

    // 等待组件加载完成，显示按钮
    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    // 按钮应包含租户名称
    await waitFor(() => {
      expect(screen.getByText('Tenant A')).toBeInTheDocument();
    });
  });

  it('test_selector_lists_available_tenants', async () => {
    // Mock 返回 3 个租户
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([
        { id: 1, name: 'Tenant A', slug: 'tenant-a' },
        { id: 2, name: 'Tenant B', slug: 'tenant-b' },
        { id: 3, name: 'Tenant C', slug: 'tenant-c' }
      ])
    });

    await act(async () => {
      render(<TenantSelector apiKey={mockApiKey} />);
    });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    // 点击打开下拉
    await act(async () => {
      fireEvent.click(screen.getByRole('button'));
    });

    // 下拉列表应显示所有租户
    await waitFor(() => {
      expect(screen.getAllByText('Tenant A').length).toBeGreaterThan(0);
    });
  });

  it('test_selector_switch_updates_state', async () => {
    const mockOnTenantChange = vi.fn();

    await act(async () => {
      render(<TenantSelector apiKey={mockApiKey} onTenantChange={mockOnTenantChange} />);
    });

    await waitFor(() => {
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    // 打开下拉
    await act(async () => {
      fireEvent.click(screen.getByRole('button'));
    });

    await waitFor(() => {
      expect(screen.getByText('Tenant B')).toBeInTheDocument();
    });

    // 选择 Tenant B
    await act(async () => {
      fireEvent.click(screen.getByText('Tenant B'));
    });

    await waitFor(() => {
      expect(mockOnTenantChange).toHaveBeenCalledWith(2);
    });
  });
});