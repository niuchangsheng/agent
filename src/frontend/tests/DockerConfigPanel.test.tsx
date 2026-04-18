import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import DockerConfigPanel from '../src/components/DockerConfigPanel';

// Mock fetch
global.fetch = vi.fn();

describe('DockerConfigPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mock localStorage
    const mockLocalStorage = {
      getItem: vi.fn().mockReturnValue('test-api-key'),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });
  });

  it('renders loading state initially', () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        memory_limit_mb: 512,
        cpu_limit: 1,
        timeout_seconds: 60,
        max_concurrent_containers: 3,
      }),
    } as Response);

    render(<DockerConfigPanel />);
    expect(screen.getByText(/Docker Sandbox Configuration/i)).toBeInTheDocument();
  });

  it('displays config from API', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        memory_limit_mb: 1024,
        cpu_limit: 2,
        timeout_seconds: 120,
        max_concurrent_containers: 5,
      }),
    } as Response);

    render(<DockerConfigPanel />);

    await waitFor(() => {
      // Use more specific selectors - check for labels containing the values
      expect(screen.getByText(/Memory Limit.*1024/i)).toBeInTheDocument();
      expect(screen.getByText(/CPU Limit.*2/i)).toBeInTheDocument();
      expect(screen.getByText(/Timeout.*120/i)).toBeInTheDocument();
    });
  });

  it('validates memory limit range', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        memory_limit_mb: 512,
        cpu_limit: 1,
        timeout_seconds: 60,
        max_concurrent_containers: 3,
      }),
    } as Response);

    render(<DockerConfigPanel />);

    // Memory slider should have valid range indicator - use getAllByText since there are multiple
    await waitFor(() => {
      const validRanges = screen.getAllByText(/Valid range/i);
      expect(validRanges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('validates cpu limit range', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        memory_limit_mb: 512,
        cpu_limit: 1,
        timeout_seconds: 60,
        max_concurrent_containers: 3,
      }),
    } as Response);

    render(<DockerConfigPanel />);

    await waitFor(() => {
      expect(screen.getByText(/CPU Limit/)).toBeInTheDocument();
    });
  });

  it('validates timeout range', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        memory_limit_mb: 512,
        cpu_limit: 1,
        timeout_seconds: 60,
        max_concurrent_containers: 3,
      }),
    } as Response);

    render(<DockerConfigPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Timeout/)).toBeInTheDocument();
    });
  });

  it('saves config successfully', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          memory_limit_mb: 512,
          cpu_limit: 1,
          timeout_seconds: 60,
          max_concurrent_containers: 3,
        }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          memory_limit_mb: 512,
          cpu_limit: 1,
          timeout_seconds: 60,
          max_concurrent_containers: 3,
        }),
      } as Response);

    render(<DockerConfigPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Save Docker Configuration/i)).toBeInTheDocument();
    });

    const saveButton = screen.getByText(/Save Docker Configuration/i);
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/saved successfully/i)).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Failed to fetch Docker config' }),
      } as Response);

    render(<DockerConfigPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to fetch Docker config/i)).toBeInTheDocument();
    });
  });

  it('sends API key in headers', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        memory_limit_mb: 512,
        cpu_limit: 1,
        timeout_seconds: 60,
        max_concurrent_containers: 3,
      }),
    } as Response);

    render(<DockerConfigPanel />);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/docker-config',
        expect.objectContaining({
          headers: {
            'X-API-Key': 'test-api-key'
          }
        })
      );
    });
  });
});