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
import TenantInfo from './components/TenantInfo';
import Toast from './components/Toast';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Task {
  id: number;
  project_id: number;
  raw_objective: string;
  status: string;
}

interface ToastState {
  message: string;
  type: ToastType;
}

type ViewMode = 'input' | 'execution' | 'advanced';

function App() {
  const [status, setStatus] = useState<string>('Detecting...');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [viewMode, setViewMode] = useState<ViewMode>('input');
  const [currentTaskId, setCurrentTaskId] = useState<number | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [panelContent, setPanelContent] = useState<'settings' | 'apikeys' | 'metrics'>('settings');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toast, setToast] = useState<ToastState | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [apiKey, setApiKey] = useState<string>('');

  useEffect(() => {
    // 获取 API Key
    const storedApiKey = localStorage.getItem('api_key');
    if (storedApiKey) {
      setApiKey(storedApiKey);
    }

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
    if (apiKey) {
      fetch('/api/v1/tasks', {
        headers: {
          'X-API-Key': apiKey
        }
      })
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
    }
  }, []);

  // Show toast notification
  const showToast = (message: string, type: ToastType) => {
    setToast({ message, type });
  };

  // 视图切换动画
  const switchView = (newMode: ViewMode) => {
    setIsTransitioning(true);
    setTimeout(() => {
      setViewMode(newMode);
      setIsTransitioning(false);
    }, 150);
  };

  // Handle task submission from SingleInputView
  const handleTaskSubmit = async (objective: string) => {
    try {
      const apiKey = localStorage.getItem('api_key');
      if (!apiKey) {
        showToast('请先创建 API Key：点击右上角 API 按钮创建', 'warning');
        // 自动打开 API Key 面板
        setPanelContent('apikeys');
        setPanelOpen(true);
        return;
      }

      setIsSubmitting(true);

      // Create API key first if needed (simplified - use existing key)
      const response = await fetch('/api/v1/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': apiKey,
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
        showToast('任务创建成功', 'success');
        // 带动画切换到执行视图
        setTimeout(() => {
          switchView('execution');
        }, 300);
      } else {
        const error = await response.json();
        console.error('Failed to create task:', error);
        showToast(`创建任务失败: ${error.detail || '未知错误'}`, 'error');
      }
    } catch (err) {
      console.error('Failed to create task:', err);
      showToast('创建任务失败: 网络错误', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render based on view mode
  if (viewMode === 'input') {
    return (
      <>
        {/* 租户信息显示在右上角左侧 */}
        <div className="fixed top-4 left-4">
          <TenantInfo apiKey={apiKey} />
        </div>
        <div className={`transition-opacity duration-150 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
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
            onAdvancedClick={() => switchView('advanced')}
            isSubmitting={isSubmitting}
          />
        </div>
        {/* 侧边面板 */}
        <SidePanel
          isOpen={panelOpen}
          onClose={() => setPanelOpen(false)}
          title={panelContent === 'settings' ? '设置' : panelContent === 'apikeys' ? 'API Keys' : '监控'}
        >
          {panelContent === 'apikeys' ? <ApiKeyManager /> : panelContent === 'metrics' ? <MetricsDashboard /> : (
            <ConfigPanel />
          )}
        </SidePanel>
        {/* Toast 通知 */}
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </>
    );
  }

  if (viewMode === 'execution' && currentTaskId) {
    return (
      <>
        <div className={`transition-opacity duration-150 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
          <LiveExecutionView
            taskId={currentTaskId}
            onComplete={() => switchView('input')}
            isCompleted={tasks.find(t => t.id === currentTaskId)?.status === 'COMPLETED'}
          />
          {/* 高级模式按钮 */}
          <button
            onClick={() => switchView('advanced')}
            className="fixed top-4 right-4 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors flex items-center gap-2"
            aria-label="高级"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 018.25 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 8.25h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
            </svg>
            <span className="text-slate-400">高级</span>
          </button>
        </div>
      </>
    );
  }

  // Advanced mode - original dashboard
  return (
    <div className={`min-h-screen bg-slate-950 text-slate-300 p-8 flex flex-col items-center transition-opacity duration-150 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
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
            onClick={() => switchView('input')}
            className="px-3 py-1 bg-cyan-600 text-white rounded-lg transition-colors hover:bg-cyan-500 flex items-center gap-2"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 17l-5-5m0 0l5-5m-5 5h12" />
            </svg>
            <span>简单模式</span>
          </button>
        </div>
      </div>

      {/* 保留原有 Dashboard 组件 */}
      {currentTaskId && (
        <div className="w-full max-w-6xl animate-view-transition">
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