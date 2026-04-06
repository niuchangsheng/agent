import React, { useEffect, useState } from 'react';

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
    <div style={{ backgroundColor: '#0f172a', color: 'white', minHeight: '100vh', padding: '20px' }}>
      <h1>SECA Control Panel</h1>
      <div>Status: <span style={{ color: status === '[Connected]' ? '#22c55e' : '#ef4444'}}>{status}</span></div>
    </div>
  );
}

export default App;
