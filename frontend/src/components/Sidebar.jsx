import React from 'react';
import logoLider from '../logo_lider.png';
import ConfigEditor from './ConfigEditor';

export default function Sidebar({ resumo = {}, isOpen = true, onToggle, onClose }) {
  return (
    <aside
      className={`fixed left-0 top-0 h-full w-72 bg-white z-50 flex flex-col shadow-card text-on-surface border-r border-border transition-transform duration-300 ease-in-out ${
        isOpen ? "translate-x-0" : "-translate-x-full pointer-events-none"
      }`}
    >
      <div className="flex flex-col flex-1 min-h-0">
        <div className="h-14 px-4 flex items-center justify-between border-b border-border shrink-0">
          <img src={logoLider} alt="Logo Líder" className="max-h-8 w-auto" />
          <button
            onClick={onClose || onToggle}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-main hover:bg-black/5 transition-colors flex items-center justify-center"
            title="Ocultar barra lateral"
            type="button"
          >
            <span className="material-symbols-outlined text-[20px]">
              dock_to_left
            </span>
          </button>
        </div>
        
        <div className="px-3 py-3 shrink-0">
          <ConfigEditor />
        </div>

        {/* Resumo por Família na Sidebar */}
        <div className="px-3 pb-4 flex-1 overflow-y-auto">
          <div className="bg-surface-canvas rounded-xl p-3 border border-border shadow-sm">
            <h3 className="font-bold text-xs mb-3 text-on-surface uppercase tracking-wider">
              Valor Comprado por Família
            </h3>
            <div className="space-y-2">
              {Object.entries(resumo).length === 0 ? (
                <div className="text-xs text-on-surface-variant">Nenhum dado disponível.</div>
              ) : (
                Object.entries(resumo).map(([familia, valor]) => (
                  <div
                    key={familia}
                    className="flex justify-between items-center pb-1.5 border-b border-border last:border-0 last:pb-0"
                  >
                    <span className="text-xs font-medium text-on-surface-variant truncate max-w-[130px]" title={familia}>
                      {familia}
                    </span>
                    <span className="text-xs font-bold text-on-surface">
                      {valor.toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                        minimumFractionDigits: 3,
                        maximumFractionDigits: 3,
                      })}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

      </div>
    </aside>
  );
}
