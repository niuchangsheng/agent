import { ReactNode } from 'react';

interface SidePanelProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

function SidePanel({ isOpen, onClose, title, children }: SidePanelProps) {
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
          className="px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-sm"
          aria-label="关闭"
        >
          关闭
        </button>
      </div>

      {/* 内容 */}
      <div className="flex-1 p-4 overflow-auto">
        {children}
      </div>
    </div>
  );
}

export default SidePanel;