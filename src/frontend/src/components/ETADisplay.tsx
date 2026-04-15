import { useEffect, useState } from 'react';

interface ETADisplayProps {
  taskId: number;
  progressUpdates: number;
  estimatedRemainingSeconds: number | null;
  estimatedCompletionAt: string | null;
}

const ETADisplay: React.FC<ETADisplayProps> = ({
  progressUpdates,
  estimatedRemainingSeconds,
  estimatedCompletionAt,
}) => {
  const [displayText, setDisplayText] = useState<string>('');

  useEffect(() => {
    // Less than 3 progress updates - show calculating
    if (progressUpdates < 3) {
      setDisplayText('计算中...');
      return;
    }

    // No ETA data available
    if (estimatedRemainingSeconds === null && estimatedCompletionAt === null) {
      setDisplayText('-');
      return;
    }

    // Format remaining time
    let timeText = '';
    if (estimatedRemainingSeconds !== null) {
      if (estimatedRemainingSeconds < 60) {
        timeText = `剩余约 ${estimatedRemainingSeconds} 秒`;
      } else {
        const minutes = Math.round(estimatedRemainingSeconds / 60);
        timeText = `剩余约 ${minutes} 分钟`;
      }
    }

    // Format completion time if available
    if (estimatedCompletionAt) {
      const completionDate = new Date(estimatedCompletionAt);
      const timeStr = completionDate.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      });
      if (timeText) {
        timeText += ` (预计 ${timeStr} 完成)`;
      } else {
        timeText = `预计 ${timeStr} 完成`;
      }
    }

    setDisplayText(timeText || '-');
  }, [progressUpdates, estimatedRemainingSeconds, estimatedCompletionAt]);

  return (
    <div className="text-sm text-slate-400">
      <span className="text-cyan-400 font-mono">{displayText}</span>
    </div>
  );
};

export default ETADisplay;
