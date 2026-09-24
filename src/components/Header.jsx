import React, { useState } from 'react';
import { apiCall } from '../services/api';

export default function Header({ totalItens }) {
  const [loading, setLoading] = useState(false);

  const handleGerarOCs = async () => {
    try {
      setLoading(true);
      await apiCall("gerar_ocs");
      alert("Ordens de Compra geradas com sucesso!");
    } catch (e) {
      alert("Erro ao gerar OCs: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <header className="fixed top-0 left-72 right-0 h-20 bg-surface-card/95 backdrop-blur-xl z-40 border-b border-border shadow-sm px-lg flex items-center justify-between">
      <h2 className="text-xl font-bold text-text-main">Procurement Analytics - Resultado da Análise</h2>
      <div className="flex items-center gap-4">
         <span className="text-sm text-text-secondary flex items-center gap-2">
           <span>Total Registros:</span>
           <span className="font-bold text-primary">{totalItens}</span>
         </span>
         <span className="text-sm text-text-secondary">AO VIVO</span>
         <button 
           onClick={handleGerarOCs}
           disabled={loading}
           className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-btn-hover disabled:opacity-50"
         >
           {loading ? 'Gerando...' : 'Gerar OCs'}
         </button>
      </div>
    </header>
  );
}
