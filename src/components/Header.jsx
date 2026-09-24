import React from 'react';

export default function Header() {
  return (
    <header className="fixed top-0 left-72 right-0 h-20 bg-surface-card/95 backdrop-blur-xl z-40 border-b border-border shadow-sm px-lg flex items-center justify-between">
      <h2 className="text-xl font-bold text-text-main">Resultado da Análise</h2>
      <div className="flex items-center gap-4">
         <span className="text-sm text-text-secondary">AO VIVO</span>
         <button className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-btn-hover">Gerar OCs</button>
      </div>
    </header>
  );
}
