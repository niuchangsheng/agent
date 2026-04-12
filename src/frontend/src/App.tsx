import { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard';
import PlaybackTree from './components/PlaybackTree';

interface Task {
  id: number;
  project_id: number;
  raw_objective: string;
  status: string;
}

function App() {
  const [status, setStatus] = useState<string>('Detecting...');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<number | null>(null);

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

    // Fetch task list
    fetch('/api/v1/tasks')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setTasks(data);
          setSelectedTaskId(data[0].id);
        }
      })
      .catch(err => {
        console.warn('Failed to fetch tasks:', err);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 p-8 flex flex-col items-center">
      <div className="w-full max-w-6xl mb-8 flex justify-between items-end border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400 font-mono tracking-wider">SECA Core Control</h1>
          <p className="text-slate-500 text-sm mt-1">Self-Evolving Coding Agent - Diagnostic HUD</p>
        </div>
        <div className="font-mono text-sm flex items-center gap-4">
          <span>
            API Link:
            <span className={`ml-2 px-2 py-1 rounded bg-slate-900 border ${status === '[Connected]' ? 'text-emerald-400 border-emerald-500/50' : 'text-red-400 border-red-500/50'}`}>
              {status}
            </span>
          </span>
          {tasks.length > 0 && (
            <select
              value={selectedTaskId || ''}
              onChange={(e) => setSelectedTaskId(Number(e.target.value))}
              className="px-2 py-1 bg-slate-900 border border-slate-700 rounded text-slate-300 text-sm"
            >
              {tasks.map(task => (
                <option key={task.id} value={task.id}>
                  Task #{task.id}: {task.status}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {selectedTaskId ? (
        <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Dashboard taskId={selectedTaskId.toString()} />
          <PlaybackTree taskId={selectedTaskId.toString()} />
        </div>
      ) : (
        <div className="text-slate-500">No tasks available. Create a task to begin.</div>
      )}
    </div>
  );
}

export default App;
