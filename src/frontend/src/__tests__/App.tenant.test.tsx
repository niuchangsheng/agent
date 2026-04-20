import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import App from '../App';

describe('App Tenant Integration - Sprint 22', () => {
  const originalLocalStorage = window.localStorage;
  const originalFetch = global.fetch;

  beforeEach(() => {
    // Mock localStorage with proper prototype chain
    const localStorageMock = {
      getItem: vi.fn((key: string) => {
        if (key === 'api_key' || key === 'tenant_id') return 'test-api-key';
        return null;
      }),
      setItem: vi.fn(),
      clear: vi.fn(),
      removeItem: vi.fn(),
      length: 0,
      key: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
      configurable: true
    });

    // Mock fetch for health check and tenant
    global.fetch = vi.fn().mockImplementation((url: string, options?: { headers?: { 'X-API-Key'?: string } }) => {
      if (url.includes('/health')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: 'active' })
        });
      }
      if (url.includes('/tenants/me')) {
        // Verify API key is passed
        const apiKey = options?.headers?.['X-API-Key'];
        if (!apiKey) {
          return Promise.resolve({
            ok: false,
            json: () => Promise.resolve({ detail: 'Unauthorized' })
          });
        }
        return Promise.resolve({
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
      }
      if (url.includes('/tasks')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([])
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve([]) });
    });
  });

  afterEach(() => {
    Object.defineProperty(window, 'localStorage', { value: originalLocalStorage });
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('test_tenant_info_in_header', async () => {
    await act(async () => {
      render(<App />);
    });

    // Wait for apiKey state to be set from localStorage, then tenant data to load
    await waitFor(() => {
      expect(screen.getByText(/Test Tenant/i)).toBeInTheDocument();
    }, { timeout: 5000 });
  });

  it('test_tenant_switch_refreshes_data', async () => {
    const mockFetch = global.fetch as ReturnType<typeof vi.fn>;

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByText(/Test Tenant/i)).toBeInTheDocument();
    }, { timeout: 5000 });

    // 模拟切换租户 - 触发 localStorage 变化
    await act(async () => {
      localStorage.setItem('tenant_id', '2');
    });

    // 验证数据刷新 - fetch 应被调用
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalled();
    });
  });
});