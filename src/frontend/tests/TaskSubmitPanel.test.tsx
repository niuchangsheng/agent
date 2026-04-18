import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TaskSubmitPanel from '../src/components/TaskSubmitPanel';

// Mock fetch
global.fetch = vi.fn();

describe('TaskSubmitPanel', () => {
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

  it('renders all form elements', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, name: 'Test Project', target_repo_path: './test' },
      ],
    } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      // Check title using role
      expect(screen.getByRole('heading', { name: /提交任务/i })).toBeInTheDocument();
      expect(screen.getByRole('combobox')).toBeInTheDocument(); // Project selector
      expect(screen.getByPlaceholderText(/任务目标/i)).toBeInTheDocument(); // Objective input
      expect(screen.getByRole('button', { name: /提交任务/i })).toBeInTheDocument();
    });
  });

  it('displays projects from API', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, name: 'Project Alpha', target_repo_path: './alpha' },
        { id: 2, name: 'Project Beta', target_repo_path: './beta' },
      ],
    } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      expect(screen.getByText('Project Alpha')).toBeInTheDocument();
      expect(screen.getByText('Project Beta')).toBeInTheDocument();
    });
  });

  it('validates required fields', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, name: 'Test Project', target_repo_path: './test' },
      ],
    } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    // Click submit without entering objective
    const submitButton = screen.getByRole('button', { name: /提交任务/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/请输入任务目标/i)).toBeInTheDocument();
    });
  });

  it('validates objective length', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, name: 'Test Project', target_repo_path: './test' },
      ],
    } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/任务目标/i)).toBeInTheDocument();
    });

    // Enter very long objective
    const textarea = screen.getByPlaceholderText(/任务目标/i);
    const longText = 'a'.repeat(600);
    fireEvent.change(textarea, { target: { value: longText } });

    await waitFor(() => {
      expect(screen.getByText(/字数超限/i)).toBeInTheDocument();
    });
  });

  it('submits task successfully', async () => {
    const mockOnTaskCreated = vi.fn();

    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { id: 1, name: 'Test Project', target_repo_path: './test' },
        ],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 10,
          project_id: 1,
          raw_objective: 'Test objective',
          status: 'PENDING',
        }),
      } as Response);

    render(<TaskSubmitPanel onTaskCreated={mockOnTaskCreated} />);

    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    // Select project and enter objective
    const projectSelect = screen.getByRole('combobox');
    fireEvent.change(projectSelect, { target: { value: '1' } });

    const textarea = screen.getByPlaceholderText(/任务目标/i);
    fireEvent.change(textarea, { target: { value: 'Test objective' } });

    // Click submit
    const submitButton = screen.getByRole('button', { name: /提交任务/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockOnTaskCreated).toHaveBeenCalled();
    });
  });

  it('handles API error gracefully', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { id: 1, name: 'Test Project', target_repo_path: './test' },
        ],
      } as Response)
      .mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'API Error' }),
      } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    // Select project and enter objective
    const projectSelect = screen.getByRole('combobox');
    fireEvent.change(projectSelect, { target: { value: '1' } });

    const textarea = screen.getByPlaceholderText(/任务目标/i);
    fireEvent.change(textarea, { target: { value: 'Test objective' } });

    // Click submit
    const submitButton = screen.getByRole('button', { name: /提交任务/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      // Component shows the actual error message from API
      expect(screen.getByText(/API Error/i)).toBeInTheDocument();
    });
  });

  it('sends API key in headers', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => [
          { id: 1, name: 'Test Project', target_repo_path: './test' },
        ],
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 10,
          project_id: 1,
          raw_objective: 'Test',
          status: 'PENDING',
        }),
      } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      expect(screen.getByText('Test Project')).toBeInTheDocument();
    });

    // Submit task
    const projectSelect = screen.getByRole('combobox');
    fireEvent.change(projectSelect, { target: { value: '1' } });

    const textarea = screen.getByPlaceholderText(/任务目标/i);
    fireEvent.change(textarea, { target: { value: 'Test' } });

    const submitButton = screen.getByRole('button', { name: /提交任务/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/tasks',
        expect.objectContaining({
          headers: expect.objectContaining({
            'X-API-Key': 'test-api-key',
          }),
        })
      );
    });
  });

  it('disables submit when no API key', async () => {
    // Mock localStorage with no API key
    const mockLocalStorage = {
      getItem: vi.fn().mockReturnValue(''),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', {
      value: mockLocalStorage,
      writable: true,
    });

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => [
        { id: 1, name: 'Test Project', target_repo_path: './test' },
      ],
    } as Response);

    render(<TaskSubmitPanel />);

    await waitFor(() => {
      expect(screen.getByText(/请先创建 API Key/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /提交任务/i })).toBeDisabled();
    });
  });
});