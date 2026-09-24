import React from 'react';

export default function MetricsCards() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-md">
       <div className="bg-surface-card p-md rounded-lg shadow-card">
          <p className="text-xs uppercase text-text-secondary font-bold">Total Geral Comprado</p>
          <h3 className="text-2xl font-bold text-text-main mt-2">R$ 4.829.350,00</h3>
       </div>
       <div className="bg-surface-card p-md rounded-lg shadow-card">
          <p className="text-xs uppercase text-text-secondary font-bold">Itens Sob Análise</p>
          <h3 className="text-2xl font-bold text-text-main mt-2">1.240</h3>
       </div>
       <div className="bg-surface-card p-md rounded-lg shadow-card">
          <p className="text-xs uppercase text-text-secondary font-bold">Decisões Editadas</p>
          <h3 className="text-2xl font-bold text-cell-edited-text mt-2">18</h3>
       </div>
       <div className="bg-surface-card p-md rounded-lg shadow-card">
          <p className="text-xs uppercase text-text-secondary font-bold">OCs Prontas para Emissão</p>
          <h3 className="text-2xl font-bold text-text-main mt-2">42</h3>
       </div>
    </div>
  );
}
