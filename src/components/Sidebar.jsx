import React from 'react';

export default function Sidebar() {
  const menuItems = [
    { name: 'Resultado da Análise', icon: 'table_chart', active: true },
    { name: 'Resumo Executivo', icon: 'insights' },
    { name: 'Ordens Geradas', icon: 'shopping_bag' },
    { name: 'Parâmetros & Regras', icon: 'tune' },
    { name: 'Log de Edição', icon: 'history' }
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-primary z-50 flex flex-col justify-between shadow-card text-white">
      <div className="flex flex-col">
        <div className="h-20 px-6 flex items-center gap-3 border-b border-white/10">
          <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-md">
            <span className="material-symbols-outlined text-white">finance_mode</span>
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">Emerald SCM</h1>
            <span className="text-xs text-white/75 uppercase tracking-wider block">Procurement</span>
          </div>
        </div>
        <div className="px-4 py-4">
          <div className="bg-white/10 rounded-xl p-3 border border-white/20 mb-4">
            <div className="flex items-center justify-between text-white/90 mb-1">
              <span className="text-xs uppercase tracking-wider">Lote Vigente</span>
              <span className="material-symbols-outlined text-[16px]">verified</span>
            </div>
            <div className="font-bold text-xl">ANL-2024-Q3</div>
          </div>
          <nav className="flex flex-col gap-1">
            {menuItems.map((item, idx) => (
              <a key={idx} href="#" className={`flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all ${item.active ? 'bg-white/20 font-bold' : 'text-white/80 hover:bg-white/10 hover:text-white'}`}>
                <span className="material-symbols-outlined text-[20px]">{item.icon}</span>
                <span className="font-medium text-sm">{item.name}</span>
              </a>
            ))}
          </nav>
        </div>
      </div>
    </aside>
  );
}
