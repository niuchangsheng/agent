import { useState, useEffect } from 'react';

interface SingleInputViewProps {
  onSubmit: (objective: string) => void;
  onSettingsClick: () => void;
  onApiKeysClick: () => void;
  onMetricsClick: () => void;
  isSubmitting?: boolean;
}

// SVG 图标组件（Heroicons 风格）
const SettingsIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.296c.55 0 1.02.398 1.11.94l.213 1.281c.153.912.832 1.636 1.744 1.79l1.281.213c.542.09.94.56.94 1.11v2.296c0 .55-.398 1.02-.94 1.11l-1.281.213c-.912.153-1.636.832-1.79 1.744l-.213 1.281c-.09.542-.56.94-1.11.94h-2.296c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.153-.912-.832-1.636-1.744-1.79l-1.281-.213c-.542-.09-.94-.56-.94-1.11V7.594c0-.55.398-1.02.94-1.11l1.281-.213c.912-.153 1.636-.832 1.79-1.744l.213-1.281Z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
  </svg>
);

const KeyIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 5.25a3 3 0 0 1 3 3m0 0v7.5a3 3 0 0 1-3 3h-7.5a3 3 0 0 1-3-3v-7.5a3 3 0 0 1 3-3h7.5a3 3 0 0 1 3 3Z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15.75 5.25v1.5a2.25 2.25 0 0 1-2.25 2.25h-1.5a2.25 2.25 0 0 1-2.25-2.25v-1.5" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 15.75v.008" />
  </svg>
);

const ChartIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
  </svg>
);

function SingleInputView({
  onSubmit,
  onSettingsClick,
  onApiKeysClick,
  onMetricsClick,
  isSubmitting = false,
}: SingleInputViewProps) {
  const [objective, setObjective] = useState('');
  const [hasApiKey, setHasApiKey] = useState(false);

  // 检测 API Key 状态
  useEffect(() => {
    const apiKey = localStorage.getItem('api_key');
    setHasApiKey(apiKey && apiKey.length > 0);
  }, []);

  const handleSubmit = () => {
    if (objective.trim() && !isSubmitting) {
      onSubmit(objective.trim());
    }
  };

  // Enter 键提交支持（Shift+Enter 换行）
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 flex flex-col items-center justify-center p-8">
      {/* 右上角图标 */}
      <div className="fixed top-4 right-4 flex gap-3">
        <button
          onClick={onSettingsClick}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
          aria-label="设置"
        >
          <SettingsIcon />
          <span className="text-slate-400">设置</span>
        </button>
        <button
          onClick={onApiKeysClick}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
          aria-label="API Key 管理"
        >
          <KeyIcon />
          <span className="text-slate-400">API</span>
        </button>
        <button
          onClick={onMetricsClick}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm flex items-center gap-2 transition-colors"
          aria-label="系统监控"
        >
          <ChartIcon />
          <span className="text-slate-400">监控</span>
        </button>
      </div>

      {/* 主标题 */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-cyan-400 font-mono tracking-wider">
          SECA Agent
        </h1>
        <p className="text-slate-500 text-sm mt-2">
          自演进编码代理 — 智能诊断与自动化修复平台
        </p>
      </div>

      {/* API Key 引导提示 */}
      {!hasApiKey && (
        <div className="w-full max-w-2xl mb-4 p-3 bg-amber-900/30 border border-amber-500/50 rounded-xl text-amber-300 text-sm flex items-center gap-2">
          <span className="text-lg">⚠</span>
          <span>首次使用？点击右上角 <strong>API</strong> 按钮创建 API Key</span>
        </div>
      )}

      {/* 输入框容器 */}
      <div className="w-full max-w-2xl flex flex-col items-center gap-4">
        <textarea
          placeholder="例如：修复登录页面的 JWT 验证错误..."
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          onKeyDown={handleKeyDown}
          className="w-full p-4 bg-slate-900/80 backdrop-blur-sm border border-slate-700 rounded-xl text-slate-300 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none min-h-32 transition-colors"
          rows={4}
          disabled={isSubmitting}
        />

        <button
          onClick={handleSubmit}
          disabled={!objective.trim() || isSubmitting}
          className="px-8 py-3 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl transition-colors flex items-center gap-2 shadow-lg shadow-cyan-500/20"
        >
          {isSubmitting ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span>提交中...</span>
            </>
          ) : (
            <span>提交</span>
          )}
        </button>

        {/* 快捷键提示 */}
        <p className="text-xs text-slate-500">
          按 <kbd className="px-1 py-0.5 bg-slate-800 rounded text-slate-400">Enter</kbd> 提交，<kbd className="px-1 py-0.5 bg-slate-800 rounded text-slate-400">Shift+Enter</kbd> 换行
        </p>
      </div>
    </div>
  );
}

export default SingleInputView;