import { useState } from 'react';

interface PrioritySelectorProps {
  taskId: number;
  value: number;
  onChange?: (value: number) => void;
}

const PrioritySelector: React.FC<PrioritySelectorProps> = ({
  taskId,
  value,
  onChange,
}) => {
  const [error, setError] = useState<string | null>(null);

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newValue = parseInt(e.target.value, 10);

    try {
      const response = await fetch(
        `/api/v1/tasks/${taskId}/priority?priority=${newValue}`,
        {
          method: 'PUT',
          headers: {
            'X-API-Key': localStorage.getItem('api_key') || '',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update priority');
      }

      setError(null);
      onChange?.(newValue);
    } catch (err) {
      setError('更新优先级失败');
      onChange?.(newValue);
    }
  };

  const isHighPriority = value >= 7;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <label className="text-sm text-slate-400">优先级:</label>
        <select
          value={value}
          onChange={handleChange}
          className={`px-2 py-1 bg-slate-900 border rounded text-slate-300 text-sm ${
            isHighPriority
              ? 'border-red-500/50 bg-red-900/20'
              : 'border-slate-700'
          }`}
        >
          {Array.from({ length: 11 }, (_, i) => (
            <option key={i} value={i}>
              {i}
            </option>
          ))}
        </select>
        {isHighPriority && (
          <span className="text-xs text-red-400">⚠️ 高优先级</span>
        )}
      </div>
      {error && (
        <span className="text-xs text-red-400">{error}</span>
      )}
    </div>
  );
};

export default PrioritySelector;
