import { useState } from 'react';

interface SingleInputViewProps {
  onSubmit: (objective: string) => void;
  onSettingsClick: () => void;
  onApiKeysClick: () => void;
  onMetricsClick: () => void;
}

function SingleInputView({
  onSubmit,
  onSettingsClick,
  onApiKeysClick,
  onMetricsClick
}: SingleInputViewProps) {
  const [objective, setObjective] = useState('');

  const handleSubmit = () => {
    if (objective.trim()) {
      onSubmit(objective.trim());
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 flex flex-col items-center justify-center p-8">
      {/* 右上角图标 */}
      <div className="fixed top-4 right-4 flex gap-2">
        <button
          onClick={onSettingsClick}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm"
          aria-label="设置"
        >
          ⚙️ 设置
        </button>
        <button
          onClick={onApiKeysClick}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm"
          aria-label="API"
        >
          🔑 API
        </button>
        <button
          onClick={onMetricsClick}
          className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm"
          aria-label="监控"
        >
          📊 监控
        </button>
      </div>

      {/* 主标题 */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-bold text-cyan-400 font-mono tracking-wider">
          SECA Agent
        </h1>
        <p className="text-slate-500 text-sm mt-2">
          Self-Evolving Coding Agent
        </p>
      </div>

      {/* 输入框容器 */}
      <div className="w-full max-w-2xl flex flex-col items-center gap-4">
        <textarea
          placeholder="输入任务目标..."
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          className="w-full p-4 bg-slate-900/80 backdrop-blur-sm border border-slate-700 rounded-xl text-slate-300 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none min-h-32"
          rows={4}
        />

        <button
          onClick={handleSubmit}
          disabled={!objective.trim()}
          className="px-8 py-3 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-medium rounded-xl transition-colors"
        >
          提交
        </button>
      </div>
    </div>
  );
}

export default SingleInputView;