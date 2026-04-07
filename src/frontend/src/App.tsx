import React, { useEffect, useState } from 'react';
import Dashboard from './components/Dashboard';
import PlaybackTree from './components/PlaybackTree';

function App() {
  const [status, setStatus] = useState<string>('Detecting...');

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
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 p-8 flex flex-col items-center">
      <div className="w-full max-w-6xl mb-8 flex justify-between items-end border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-3xl font-bold text-cyan-400 font-mono tracking-wider">SECA Core Control</h1>
          <p className="text-slate-500 text-sm mt-1">Self-Evolving Coding Agent - Diagnostic HUD</p>
        </div>
        <div className="font-mono text-sm">
          API Link: 
          <span className={`ml-2 px-2 py-1 rounded bg-slate-900 border ${status === '[Connected]' ? 'text-emerald-400 border-emerald-500/50' : 'text-red-400 border-red-500/50'}`}>
            {status}
          </span>
        </div>
      </div>

      <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Dashboard taskId="1" />
        <PlaybackTree taskId="1" />
      </div>
    </div>
  );
}

export default App;
