import { useEffect, useState } from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
  duration?: number;
}

const typeStyles: Record<ToastType, string> = {
  success: 'bg-emerald-900/30 border-emerald-500/50 text-emerald-300',
  error: 'bg-red-900/30 border-red-500/50 text-red-300',
  warning: 'bg-amber-900/30 border-amber-500/50 text-amber-300',
  info: 'bg-cyan-900/30 border-cyan-500/50 text-cyan-300',
};

const typeIcons: Record<ToastType, string> = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
};

function Toast({ message, type, onClose, duration = 3000 }: ToastProps) {
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // 显示一段时间后开始退出动画
    const exitTimer = setTimeout(() => {
      setIsExiting(true);
    }, duration - 200); // 留 200ms 给退出动画

    // 退出动画完成后调用 onClose
    const closeTimer = setTimeout(onClose, duration);

    return () => {
      clearTimeout(exitTimer);
      clearTimeout(closeTimer);
    };
  }, [duration, onClose]);

  return (
    <div
      role="alert"
      className={`fixed top-4 left-1/2 -translate-x-1/2 z-50 px-4 py-3 rounded-xl border backdrop-blur-md shadow-lg flex items-center gap-3 ${
        isExiting ? 'animate-fade-out' : 'animate-fade-in'
      } ${typeStyles[type]}`}
    >
      <span className="text-lg">{typeIcons[type]}</span>
      <span className="text-sm font-medium">{message}</span>
      <button
        onClick={() => {
          setIsExiting(true);
          setTimeout(onClose, 200);
        }}
        className="ml-2 text-slate-400 hover:text-slate-200 transition-colors"
        aria-label="关闭通知"
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export default Toast;
export type { ToastType, ToastProps };