import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import PrioritySelector from '../src/components/PrioritySelector';

// Mock fetch
global.fetch = vi.fn();

describe('PrioritySelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: vi.fn(),
    } as Response);
  });

  it('renders select with 0-10 options', () => {
    render(<PrioritySelector taskId={1} value={0} onChange={() => {}} />);

    const select = screen.getByRole('combobox');
    expect(select).toBeInTheDocument();

    // Check all options 0-10 are present
    for (let i = 0; i <= 10; i++) {
      expect(screen.getByText(i.toString())).toBeInTheDocument();
    }
  });

  it('shows current value correctly', () => {
    render(<PrioritySelector taskId={1} value={5} onChange={() => {}} />);
    expect(screen.getByRole('combobox')).toHaveValue('5');
  });

  it('applies high priority warning style for priority >= 7', () => {
    const { rerender } = render(<PrioritySelector taskId={1} value={5} onChange={() => {}} />);
    const select = screen.getByRole('combobox');
    expect(select.className).not.toContain('border-red-500');

    rerender(<PrioritySelector taskId={1} value={7} onChange={() => {}} />);
    const highPrioritySelect = screen.getByRole('combobox');
    expect(highPrioritySelect.className).toContain('border-red-500');
  });

  it('calls onChange when value changes', async () => {
    const handleChange = vi.fn();
    render(<PrioritySelector taskId={1} value={0} onChange={handleChange} />);

    const select = screen.getByRole('combobox');
    await fireEvent.change(select, { target: { value: '8' } });

    expect(handleChange).toHaveBeenCalledWith(8);
  });

  it('calls API to update priority when value changes', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: vi.fn(),
    } as Response);

    render(<PrioritySelector taskId={1} value={0} onChange={() => {}} />);

    const select = screen.getByRole('combobox');
    await fireEvent.change(select, { target: { value: '9' } });

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/tasks/1/priority?priority=9',
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  it('shows error toast when API call fails', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 401,
    } as Response);

    render(<PrioritySelector taskId={1} value={0} onChange={() => {}} />);

    const select = screen.getByRole('combobox');
    await fireEvent.change(select, { target: { value: '10' } });

    await waitFor(() => {
      expect(screen.getByText('更新优先级失败')).toBeInTheDocument();
    });
  });
});
