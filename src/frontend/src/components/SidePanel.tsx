import { ReactNode, useEffect } from 'react';

interface SidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

function SidePanel({ isOpen, onClose, title, children }: SidePanelProps) {
  // Esc 键关闭支持
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      data-testid="side-panel"
      className="fixed right-0 top-0 h-full w-80 bg-slate-900/95 backdrop-blur-sm border-l border-slate-700 z-50 flex flex-col"
    >
      {/* 头部 */}
      <div className="flex justify-between items-center p-4 border-b border-slate-700">
        <h2 className="text-lg font-medium text-cyan-400">{title}</h2>
        <button
          onClick={onClose}
          className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors group"
          aria-label="关闭面板"
          title="关闭 (Esc)"
        >
          <svg
            className="w-5 h-5 text-slate-400 group-hover:text-slate-200"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* 内容 */}
      <div className="flex-1 p-4 overflow-auto custom-scrollbar">
        {children}
      </div>
    </div>
  );
}

export default SidePanel;