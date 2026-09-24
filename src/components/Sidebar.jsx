import React from 'react';
import logoLider from '../logo_lider.png';
import ConfigEditor from './ConfigEditor';

export default function Sidebar({ resumo = {} }) {
  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-white z-50 flex flex-col shadow-card text-on-surface overflow-y-auto border-r border-border">
      <div className="flex flex-col flex-1">
        <div className="h-20 px-6 flex items-center justify-center border-b border-border shrink-0">
          <img src={logoLider} alt="Logo Líder" className="max-h-12 w-auto" />
        </div>
        
        <div className="px-4 py-4 shrink-0">
          <ConfigEditor />
        </div>

        {/* Resumo por Família na Sidebar */}
        <div className="px-4 pb-6 flex-1">
          <div className="bg-surface-canvas rounded-xl p-4 border border-border shadow-sm">
            <h3 className="font-bold text-sm mb-4 text-on-surface uppercase tracking-wider">
              Valor Comprado por Família
            </h3>
            <div className="space-y-3">
              {Object.entries(resumo).length === 0 ? (
                <div className="text-sm text-on-surface-variant">Nenhum dado disponível.</div>
              ) : (
                Object.entries(resumo).map(([familia, valor]) => (
                  <div
                    key={familia}
                    className="flex justify-between items-center pb-2 border-b border-border last:border-0 last:pb-0"
                  >
                    <span className="text-sm font-medium text-on-surface-variant">{familia}</span>
                    <span className="text-sm font-bold text-on-surface">
                      {valor.toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
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
