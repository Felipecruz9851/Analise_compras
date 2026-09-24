import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { apiCall } from '../services/api';

export default function Header({ totalItens }) {
  const [loading, setLoading] = useState(false);
  const [exportsModalOpen, setExportsModalOpen] = useState(false);
  const [exportsList, setExportsList] = useState([]);
  const [selectedExports, setSelectedExports] = useState({});

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

  const abrirExports = async () => {
    setExportsModalOpen(true);
    try {
      const lista = await apiCall('listar_exports');
      setExportsList(lista || []);
    } catch(e) {
      alert("Erro ao listar exportações: " + e.message);
    }
  };

  const baixarSelecionados = async () => {
    const arquivos = Object.keys(selectedExports).filter(k => selectedExports[k]);
    if (arquivos.length === 0) return alert("Selecione pelo menos um arquivo.");
    try {
      const resp = await apiCall('baixar_zip', { arquivos });
      if (resp.erro) throw new Error(resp.erro);
      const a = document.createElement('a');
      a.href = resp.url;
      a.download = resp.url.split('/').pop();
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch(e) {
      alert("Erro ao baixar: " + e.message);
    }
  };

  const excluirSelecionados = async () => {
    const arquivos = Object.keys(selectedExports).filter(k => selectedExports[k]);
    if (arquivos.length === 0) return alert("Selecione pelo menos um arquivo.");
    if (!window.confirm(`Deseja excluir ${arquivos.length} arquivo(s)?`)) return;
    try {
      const resp = await apiCall('excluir_exports', { arquivos });
      if (resp.erro) throw new Error(resp.erro);
      abrirExports();
    } catch(e) {
      alert("Erro ao excluir: " + e.message);
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
         <span className="text-sm text-text-secondary mr-2">AO VIVO</span>
         {totalItens > 0 && (
           <>
             <button 
               onClick={handleGerarOCs}
               disabled={loading}
               className="bg-primary hover:bg-primary-light text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-btn-hover disabled:opacity-50 transition-colors"
             >
               {loading ? 'Gerando...' : 'Gerar OCs'}
             </button>
             <button 
               onClick={abrirExports}
               className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-btn-hover transition-colors"
             >
               Exportações
             </button>
           </>
         )}
      </div>

      {exportsModalOpen && createPortal(
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[9999]">
          <div className="bg-white w-[800px] max-w-full rounded-lg shadow-2xl flex flex-col max-h-[90vh] mx-4">
            <div className="p-4 border-b flex justify-between items-center bg-gray-50 rounded-t-lg">
              <h3 className="font-bold text-lg">📁 Exportações Geradas</h3>
              <button onClick={() => setExportsModalOpen(false)} className="text-gray-500 hover:text-black font-bold text-xl">&times;</button>
            </div>
            <div className="p-4 overflow-y-auto flex-1 min-h-[300px]">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b">
                     <th className="p-2 text-center w-10"><input type="checkbox" onChange={e => {
                        const all = {};
                        exportsList.forEach(c => all[c.nome] = e.target.checked);
                        setSelectedExports(all);
                     }} /></th>
                     <th className="p-2">Nome</th><th className="p-2">Tamanho</th><th className="p-2">Data</th><th className="p-2 text-center">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {exportsList.length === 0 && (
                    <tr><td colSpan="5" className="p-4 text-center text-gray-500">Nenhum arquivo encontrado.</td></tr>
                  )}
                  {exportsList.map(c => (
                    <tr key={c.nome} className="border-b hover:bg-gray-50">
                      <td className="p-2 text-center"><input type="checkbox" checked={!!selectedExports[c.nome]} onChange={e => setSelectedExports({...selectedExports, [c.nome]: e.target.checked})} /></td>
                      <td className="p-2">{c.nome}</td><td className="p-2">{c.tamanho}</td><td className="p-2">{c.data_criacao}</td>
                      <td className="p-2 text-center"><a href={c.url} download={c.nome} className="bg-primary hover:bg-primary-light text-white px-3 py-1 rounded text-xs no-underline transition-colors">Download</a></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t flex justify-between bg-gray-50 rounded-b-lg">
              <div className="gap-2 flex">
                <button onClick={baixarSelecionados} className="bg-gray-800 hover:bg-gray-900 text-white px-4 py-2 rounded transition-colors font-semibold text-sm">⬇ Baixar Selecionados</button>
                <button onClick={excluirSelecionados} className="bg-status-danger hover:bg-red-700 text-white px-4 py-2 rounded transition-colors font-semibold text-sm">🗑 Excluir Selecionados</button>
              </div>
              <button onClick={() => setExportsModalOpen(false)} className="border px-4 py-2 rounded bg-white hover:bg-gray-100 font-semibold text-sm transition-colors">Fechar</button>
            </div>
          </div>
        </div>,
        document.body
      )}
    </header>
  );
}
