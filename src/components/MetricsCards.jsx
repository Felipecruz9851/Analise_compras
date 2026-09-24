import React from 'react';

export default function MetricsCards({ totalGeral = 0, totalItens = 0, edicoesCount = 0 }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-md">
       <div className="bg-surface-card p-md rounded-lg shadow-card border-l-4 border-primary">
          <p className="text-xs uppercase text-text-secondary font-bold">Total Geral Comprado</p>
          <h3 className="text-2xl font-bold text-text-main mt-2">
            {totalGeral.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </h3>
       </div>
       <div className="bg-surface-card p-md rounded-lg shadow-card border-l-4 border-tertiary">
          <p className="text-xs uppercase text-text-secondary font-bold">Itens Sob Análise</p>
          <h3 className="text-2xl font-bold text-text-main mt-2">{totalItens}</h3>
       </div>
       <div className="bg-surface-card p-md rounded-lg shadow-card border-l-4 border-cell-edited-border">
          <p className="text-xs uppercase text-text-secondary font-bold">Decisões Editadas</p>
          <h3 className="text-2xl font-bold text-cell-edited-text mt-2">{edicoesCount}</h3>
       </div>
       <div className="bg-surface-card p-md rounded-lg shadow-card border-l-4 border-border">
          <p className="text-xs uppercase text-text-secondary font-bold">OCs Prontas para Emissão</p>
          <h3 className="text-2xl font-bold text-text-main mt-2">--</h3>
       </div>
    </div>
  );
}
