import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import SidePanel from '../SidePanel';

describe('SidePanel', () => {
  const mockOnClose = vi.fn();

  it('test_panel_slides_from_right', () => {
    render(
      <SidePanel isOpen={true} onClose={mockOnClose} title="Settings">
        <div>Settings content</div>
      </SidePanel>
    );

    // 验证面板显示
    const panel = screen.getByTestId('side-panel');
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveClass('right-0'); // 从右侧滑出
  });

  it('test_panel_doesnt_cover_main_view', () => {
    render(
      <SidePanel isOpen={true} onClose={mockOnClose} title="Settings">
        <div>Settings content</div>
      </SidePanel>
    );

    // 验证面板宽度 ≤ 30%
    const panel = screen.getByTestId('side-panel');
    expect(panel).toHaveClass('w-80'); // 320px，约 20-30% 宽度
  });

  it('test_close_button_returns_to_main', () => {
    render(
      <SidePanel isOpen={true} onClose={mockOnClose} title="Settings">
        <div>Settings content</div>
      </SidePanel>
    );

    // 验证关闭按钮
    const closeButton = screen.getByRole('button', { name: /关闭/i });
    expect(closeButton).toBeInTheDocument();

    // 点击关闭
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalled();
  });
});