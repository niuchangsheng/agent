import { useEffect, useState, useRef } from 'react';

interface TraceStep {
  id: number;
  agent_role: string;
  perception_log?: string;
  reasoning_log?: string;
  applied_patch?: string;
  is_success: boolean;
  timestamp?: string;
}

interface TracePlaybackProps {
  taskId: number;
  autoPlay?: boolean;
  defaultSpeed?: number;
}

const TracePlayback: React.FC<TracePlaybackProps> = ({
  taskId,
  autoPlay = false,
  defaultSpeed = 1,
}) => {
  const [traces, setTraces] = useState<TraceStep[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [speed, setSpeed] = useState(defaultSpeed);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const playIntervalRef = useRef<number | null>(null);

  useEffect(() => {
    fetchTraces();
  }, [taskId]);

  // 播放控制
  useEffect(() => {
    if (isPlaying && traces.length > 0) {
      const intervalMs = 1000 / speed; // 倍速控制
      playIntervalRef.current = window.setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= traces.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, intervalMs);
    } else {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
        playIntervalRef.current = null;
      }
    }

    return () => {
      if (playIntervalRef.current) {
        clearInterval(playIntervalRef.current);
      }
    };
  }, [isPlaying, speed, traces.length]);

  const fetchTraces = async () => {
    setLoading(true);
    setError(null);

    const apiKey = localStorage.getItem('api_key') || '';

    try {
      const res = await fetch(`/api/v1/tasks/${taskId}/traces`, {
        headers: {
          'X-API-Key': apiKey,
        },
      });

      if (!res.ok) throw new Error('Failed to fetch traces');
      const data = await res.json();
      setTraces(data);
      setCurrentStep(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch traces');
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleSpeedChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSpeed(Number(e.target.value));
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentStep(Number(e.target.value));
  };

  const currentTrace = traces[currentStep];

  return (
    <div className="w-full backdrop-blur-md bg-slate-900/50 p-6 rounded-xl border border-cyan-500/30 shadow-2xl shadow-cyan-900/20">
      <h2 className="text-xl mb-4 border-b border-slate-700 pb-2 text-white">
        🎬 Trace 回放播放器
        <span className="text-sm text-slate-500 ml-2">Task #{taskId}</span>
      </h2>

      {loading && (
        <div className="text-slate-500 animate-pulse">加载 Trace 数据...</div>
      )}

      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded text-red-300 text-sm">
          {error}
        </div>
      )}

      {!loading && traces.length === 0 && (
        <div className="text-slate-500 text-center py-8">
          暂无 Trace 数据
        </div>
      )}

      {!loading && traces.length > 0 && (
        <div className="space-y-4">
          {/* 控制栏 */}
          <div className="flex items-center gap-4 flex-wrap">
            {/* 播放/暂停按钮 */}
            <button
              onClick={handlePlayPause}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded text-white flex items-center gap-2"
            >
              {isPlaying ? (
                <span>⏸️ 暂停</span>
              ) : (
                <span>▶️ 播放</span>
              )}
            </button>

            {/* 倍速选择器 */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-slate-400">倍速:</label>
              <select
                value={speed}
                onChange={handleSpeedChange}
                className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-slate-300"
              >
                <option value={0.5}>0.5x</option>
                <option value={1}>1x</option>
                <option value={2}>2x</option>
                <option value={5}>5x</option>
              </select>
              <span className="text-xs text-cyan-400">{speed}x</span>
            </div>

            {/* 进度显示 */}
            <div className="text-sm text-slate-400">
              步骤 {currentStep + 1} / {traces.length}
            </div>
          </div>

          {/* 时间轴滑块 */}
          <div>
            <input
              type="range"
              min={0}
              max={traces.length - 1}
              value={currentStep}
              onChange={handleSliderChange}
              className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* 当前步骤详情 */}
          {currentTrace && (
            <div
              className={`p-4 rounded-lg border ${
                currentTrace.is_success
                  ? 'border-emerald-500/50 bg-emerald-900/20'
                  : 'border-red-500/50 bg-red-900/20'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-white font-medium">
                  [{currentTrace.agent_role}] Trace #{currentTrace.id}
                </span>
                <span className="text-xs text-slate-500">
                  {currentTrace.timestamp}
                </span>
              </div>

              {/* Perception */}
              {currentTrace.perception_log && (
                <div className="mb-2">
                  <span className="text-xs text-cyan-400">Perception:</span>
                  <p className="text-slate-300 text-sm mt-1">
                    {currentTrace.perception_log}
                  </p>
                </div>
              )}

              {/* Reasoning */}
              {currentTrace.reasoning_log && (
                <div className="mb-2">
                  <span className="text-xs text-purple-400">Reasoning:</span>
                  <p className="text-slate-300 text-sm mt-1">
                    {currentTrace.reasoning_log}
                  </p>
                </div>
              )}

              {/* Applied Patch */}
              {currentTrace.applied_patch && (
                <div>
                  <span className="text-xs text-emerald-400">Applied Patch:</span>
                  <pre className="text-slate-300 text-xs mt-1 bg-slate-950 p-2 rounded overflow-x-auto">
                    {currentTrace.applied_patch.slice(0, 200)}
                    {currentTrace.applied_patch.length > 200 && '...'}
                  </pre>
                </div>
              )}
            </div>
          )}

          {/* 步骤列表 */}
          <div className="max-h-64 overflow-y-auto custom-scrollbar">
            <div className="text-sm text-slate-400 mb-2">步骤列表:</div>
            <div className="space-y-1">
              {traces.map((trace, index) => (
                <div
                  key={trace.id}
                  onClick={() => setCurrentStep(index)}
                  className={`p-2 rounded cursor-pointer text-sm ${
                    index === currentStep
                      ? 'bg-cyan-500/20 border border-cyan-500/50'
                      : 'bg-slate-800/50 hover:bg-slate-700/50'
                  }`}
                >
                  <span className="text-slate-300">
                    {index + 1}. [{trace.agent_role}]
                  </span>
                  <span
                    className={`ml-2 ${
                      trace.is_success ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    {trace.is_success ? '✓' : '✗'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TracePlayback;