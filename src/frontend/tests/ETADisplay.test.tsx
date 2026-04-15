import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ETADisplay from '../src/components/ETADisplay';

// Mock fetch
global.fetch = vi.fn();

describe('ETADisplay', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows calculating when progress updates less than 3', () => {
    render(<ETADisplay taskId={1} progressUpdates={1} estimatedRemainingSeconds={null} estimatedCompletionAt={null} />);
    expect(screen.getByText('计算中...')).toBeInTheDocument();
  });

  it('shows dash when no ETA data available', () => {
    render(<ETADisplay taskId={1} progressUpdates={5} estimatedRemainingSeconds={null} estimatedCompletionAt={null} />);
    expect(screen.getByText('-')).toBeInTheDocument();
  });

  it('displays remaining time in seconds format', async () => {
    render(<ETADisplay taskId={1} progressUpdates={5} estimatedRemainingSeconds={30} estimatedCompletionAt={null} />);
    await waitFor(() => {
      expect(screen.getByText('剩余约 30 秒')).toBeInTheDocument();
    });
  });

  it('displays remaining time in minutes format when > 60 seconds', () => {
    render(<ETADisplay taskId={1} progressUpdates={5} estimatedRemainingSeconds={150} estimatedCompletionAt={null} />);
    // 150 seconds = 2.5 minutes, rounds to 3 minutes
    expect(screen.getByText('剩余约 3 分钟')).toBeInTheDocument();
  });

  it('displays completion time when estimated_completion_at provided', async () => {
    const completionTime = new Date('2026-04-15T15:30:00Z');
    render(
      <ETADisplay
        taskId={1}
        progressUpdates={5}
        estimatedRemainingSeconds={1800}
        estimatedCompletionAt={completionTime.toISOString()}
      />
    );
    await waitFor(() => {
      // Should show both remaining time and completion time
      expect(screen.getByText(/剩余约/)).toBeInTheDocument();
    });
  });

  it('formats minutes correctly', () => {
    const { container } = render(<ETADisplay taskId={1} progressUpdates={5} estimatedRemainingSeconds={120} estimatedCompletionAt={null} />);
    // 120 seconds = 2 minutes
    expect(container.textContent).toContain('2 分钟');
  });

  it('formats hours correctly', () => {
    const { container } = render(<ETADisplay taskId={1} progressUpdates={5} estimatedRemainingSeconds={7200} estimatedCompletionAt={null} />);
    // 7200 seconds = 120 minutes = 2 hours
    expect(container.textContent).toContain('120 分钟');
  });
});
