import React, { useState } from 'react';
import Login from './components/Login';
import Dashboard from './components/Dashboard';

export default function App() {
  const [view, setView] = useState('login'); 

  return (
    <>
      {view === 'login' && <Login onAnalysisReady={() => setView('dashboard')} />}
      {view === 'dashboard' && <Dashboard />}
    </>
  );
}
