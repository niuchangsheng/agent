import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import TenantInfo from '../TenantInfo';

describe('TenantInfo', () => {
  const mockApiKey = 'test-api-key';

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  it('test_tenant_info_displays_name', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        id: 1,
        name: 'Test Tenant',
        slug: 'test-tenant',
        quota_tasks: 100,
        quota_storage_mb: 1024,
        quota_api_calls: 10000,
        is_active: true
      })
    }));

    render(<TenantInfo apiKey={mockApiKey} />);

    await waitFor(() => {
      expect(screen.getByText(/Test Tenant/i)).toBeInTheDocument();
    });
  });

  it('test_tenant_info_displays_quota', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        id: 1,
        name: 'Test Tenant',
        slug: 'test-tenant',
        quota_tasks: 100,
        quota_storage_mb: 1024,
        quota_api_calls: 10000,
        is_active: true
      })
    }));

    render(<TenantInfo apiKey={mockApiKey} />);

    await waitFor(() => {
      // 验证配额信息显示
      expect(screen.getByText(/100/i)).toBeInTheDocument(); // quota_tasks
      expect(screen.getByText(/1024/i)).toBeInTheDocument(); // quota_storage_mb
    });
  });

  it('test_tenant_info_fetches_from_api', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        id: 1,
        name: 'Test Tenant',
        slug: 'test-tenant',
        quota_tasks: 100,
        quota_storage_mb: 1024,
        quota_api_calls: 10000,
        is_active: true
      })
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TenantInfo apiKey={mockApiKey} />);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/tenants/me', {
        headers: {
          'X-API-Key': mockApiKey
        }
      });
    });
  });

  it('test_tenant_info_handles_error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ detail: 'Unauthorized' })
    }));

    render(<TenantInfo apiKey={mockApiKey} />);

    await waitFor(() => {
      // 错误时应显示友好提示
      expect(screen.getByText(/未授权|请先登录|无租户信息/i)).toBeInTheDocument();
    });
  });
});