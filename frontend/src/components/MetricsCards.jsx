import React from 'react';

export default function MetricsCards({
  totalGeral = 0,
  totalItens = 0,
  edicoesCount = 0,
  totalOcsProntas = 0,
  onFilterEdicoes,
  isFilteredEdicoes,
  onFilterOcs,
  isFilteredOcs,
}) {
  return (
    <div className="grid grid-cols-2 xl:grid-cols-4 gap-2">
      {/* KPI 1: OCs Prontas (Primeiro à esquerda) */}
      <div
        className={`py-1.5 px-3 rounded-lg shadow-sm border cursor-pointer transition-colors flex items-center justify-between border-l-4 ${
          isFilteredOcs
            ? 'bg-primary/10 border-primary border-l-primary'
            : 'bg-surface-card border-border border-l-border hover:bg-row-alt'
        }`}
        onClick={onFilterOcs}
        title="Filtrar apenas OCs prontas"
      >
        <div className="min-w-0">
          <p className="text-[10px] uppercase text-text-secondary font-bold tracking-wider truncate">
            OCs Prontas
          </p>
          <h3 className="text-sm sm:text-base font-bold text-text-main truncate mt-0.5">
            {totalOcsProntas}
          </h3>
        </div>
        <span className="material-symbols-outlined text-[18px] text-primary/70 shrink-0 ml-2">
          verified
        </span>
      </div>

      {/* KPI 2: Total Geral Comprado */}
      <div className="bg-surface-card py-1.5 px-3 rounded-lg shadow-sm border border-border border-l-4 border-l-primary flex items-center justify-between">
        <div className="min-w-0">
          <p className="text-[10px] uppercase text-text-secondary font-bold tracking-wider truncate">
            Total Geral Comprado
          </p>
          <h3 className="text-sm sm:text-base font-bold text-text-main truncate mt-0.5">
            {Number(totalGeral || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 3, maximumFractionDigits: 3 })}
          </h3>
        </div>
        <span className="material-symbols-outlined text-[18px] text-primary/70 shrink-0 ml-2">
          payments
        </span>
      </div>

      {/* KPI 3: Itens Sob Análise */}
      <div className="bg-surface-card py-1.5 px-3 rounded-lg shadow-sm border border-border border-l-4 border-l-tertiary flex items-center justify-between">
        <div className="min-w-0">
          <p className="text-[10px] uppercase text-text-secondary font-bold tracking-wider truncate">
            Itens Sob Análise
          </p>
          <h3 className="text-sm sm:text-base font-bold text-text-main truncate mt-0.5">
            {totalItens.toLocaleString('pt-BR')}
          </h3>
        </div>
        <span className="material-symbols-outlined text-[18px] text-tertiary/70 shrink-0 ml-2">
          inventory_2
        </span>
      </div>

      {/* KPI 4: Decisões Editadas */}
      <div
        className={`py-1.5 px-3 rounded-lg shadow-sm border cursor-pointer transition-colors flex items-center justify-between border-l-4 border-l-cell-edited-border ${
          isFilteredEdicoes
            ? 'bg-cell-edited-bg border-cell-edited-border'
            : 'bg-surface-card border-border hover:bg-row-alt'
        }`}
        onClick={onFilterEdicoes}
        title="Filtrar apenas itens editados"
      >
        <div className="min-w-0">
          <p className="text-[10px] uppercase text-text-secondary font-bold tracking-wider truncate">
            Decisões Editadas
          </p>
          <h3 className="text-sm sm:text-base font-bold text-cell-edited-text truncate mt-0.5">
            {edicoesCount}
          </h3>
        </div>
        <span className="material-symbols-outlined text-[18px] text-cell-edited-border shrink-0 ml-2">
          edit_note
        </span>
      </div>
    </div>
  );
}
