import { useEffect, useState } from 'react';
import SingleInputView from './components/SingleInputView';
import LiveExecutionView from './components/LiveExecutionView';
import SidePanel from './components/SidePanel';
import Dashboard from './components/Dashboard';
import PlaybackTree from './components/PlaybackTree';
import ConfigPanel from './components/ConfigPanel';
import TaskQueueDashboard from './components/TaskQueueDashboard';
import ApiKeyManager from './components/ApiKeyManager';
import MetricsDashboard from './components/MetricsDashboard';

interface Task {
  id: number;
  project_id: number;
  raw_objective: string;
  status: string;
}

type ViewMode = 'input' | 'execution' | 'advanced';

function App() {
  const [status, setStatus] = useState<string>('Detecting...');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('input');
  const [currentTaskId, setCurrentTaskId] = useState<number | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelContent, setPanelContent] = useState<'settings' | 'apikeys' | 'metrics'>('settings');

  useEffect(() => {
    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'active') {
          setStatus('[Connected]');
        }
      })
      .catch(() => {
        setStatus('[Disconnected]');
      });

    // Fetch task list to check for running tasks
    fetch('/api/v1/tasks')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setTasks(data);
          // Check for running tasks - if any, show execution view
          const runningTask = data.find(t => t.status === 'RUNNING');
          if (runningTask) {
            setCurrentTaskId(runningTask.id);
            setViewMode('execution');
          } else if (data.length > 0) {
            setCurrentTaskId(data[0].id);
          }
        }
      })
      .catch(err => {
        console.warn('Failed to fetch tasks:', err);
      });
  }, []);

  // Handle task submission from SingleInputView
  const handleTaskSubmit = async (objective: string) => {
    try {
      // Create API key first if needed (simplified - use existing key)
      const response = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_id: 1, // Default project
          raw_objective: objective,
          priority: 5
        })
      });

      if (response.ok) {
        const task = await response.json();
        setTasks(prev => [...prev, task]);
        setCurrentTaskId(task.id);
        setViewMode('execution');
      }
    } catch (err) {
      console.error('Failed to create task:', err);
    }
  };

  // Render based on view mode
  if (viewMode === 'input') {
    return (
      <>
        <SingleInputView
          onSubmit={handleTaskSubmit}
          onSettingsClick={() => {
            setPanelContent('settings');
            setPanelOpen(true);
          }}
          onApiKeysClick={() => {
            setPanelContent('apikeys');
            setPanelOpen(true);
          }}
          onMetricsClick={() => {
            setPanelContent('metrics');
            setPanelOpen(true);
          }}
        />
        {/* 高级模式按钮 */}
        <button
          onClick={() => setViewMode('advanced')}
          className="fixed bottom-4 right-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm"
          aria-label="高级"
        >
          高级模式
        </button>
        {/* 侧边面板 */}
        <SidePanel
          isOpen={panelOpen}
          onClose={() => setPanelOpen(false)}
          title={panelContent === 'settings' ? '设置' : panelContent === 'apikeys' ? 'API Keys' : '监控'}
        >
          {panelContent === 'apikeys' ? <ApiKeyManager /> : panelContent === 'metrics' ? <MetricsDashboard /> : (
            <div className="text-slate-500">配置设置面板内容...</div>
          )}
        </SidePanel>
      </>
    );
  }

  if (viewMode === 'execution' && currentTaskId) {
    return (
      <>
        <LiveExecutionView
          taskId={currentTaskId}
          onComplete={() => setViewMode('input')}
          isCompleted={tasks.find(t => t.id === currentTaskId)?.status === 'COMPLETED'}
        />
        {/* 高级模式按钮 */}
        <button
          onClick={() => setViewMode('advanced')}
          className="fixed bottom-4 right-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm"
          aria-label="高级"
        >
          高级模式
        </button>
      </>
    );
  }

  // Advanced mode - original dashboard
  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 p-8 flex flex-col items-center">
      <div className="w-full max-w-6xl mb-8 flex justify-between items-end border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400 font-mono tracking-wider">SECA Core Control</h1>
          <p className="text-slate-500 text-sm mt-1">Self-Evolving Coding Agent - Diagnostic HUD (Advanced)</p>
        </div>
        <div className="font-mono text-sm flex items-center gap-4">
          <span>
            API Link:
            <span className={`ml-2 px-2 py-1 rounded bg-slate-900 border ${status === '[Connected]' ? 'text-emerald-400 border-emerald-500/50' : 'text-red-400 border-red-500/50'}`}>
              {status}
            </span>
          </span>
          {/* 返回简单模式按钮 */}
          <button
            onClick={() => setViewMode('input')}
            className="px-3 py-1 bg-cyan-600 text-white rounded"
          >
            简单模式
          </button>
        </div>
      </div>

      {/* 保留原有 Dashboard 组件 */}
      {currentTaskId && (
        <div className="w-full max-w-6xl">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Dashboard taskId={currentTaskId.toString()} />
            <PlaybackTree taskId={currentTaskId.toString()} />
          </div>
        </div>
      )}
    </div>
  );
}

export default App;