import React, { useState, useEffect } from 'react';
import { apiCall, listarAnalises } from '../services/api';

export default function Login({ onAnalysisReady }) {
  const [analises, setAnalises] = useState([]);
  const [user, setUser] = useState('');
  const [pass, setPass] = useState('');
  const [analiseSelecionada, setAnaliseSelecionada] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [pickles, setPickles] = useState([]);
  
  // CSV Modal State
  const [csvModalOpen, setCsvModalOpen] = useState(false);
  const [csvList, setCsvList] = useState([]);
  const [selectedCsvs, setSelectedCsvs] = useState({});

  useEffect(() => {
    carregarAnalises();
    loadPickles();
  }, []);

  const carregarAnalises = async () => {
    try {
      const data = await listarAnalises();
      setAnalises(data);
      if (data.length > 0) setAnaliseSelecionada(data[0]);
    } catch(e) {
      const defaultAnalises = ["Compra para estoque", "compra por necessidade", "rev", "lam"];
      setAnalises(defaultAnalises);
      setAnaliseSelecionada(defaultAnalises[0]);
    }
  };

  const loadPickles = async () => {
    try {
      const lista = await apiCall('listar_pickles');
      if (lista && !lista.erro) setPickles(lista);
    } catch (e) {
      console.error(e);
    }
  };

  const executarAnalise = async () => {
    setLoading(true);
    setLoadingMsg('Executando análise...');
    try {
      const payload = { username: user, password: pass, analise: analiseSelecionada };
      await apiCall("rodar_analise", payload);
      // Backend sets up the session slice data, we can now transition
      onAnalysisReady();
    } catch(e) {
      alert("Erro ao executar: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const gerarDados = async () => {
    setLoading(true);
    setLoadingMsg('Coletando dados...');
    try {
      await apiCall('gerar_pickles', { username: user, password: pass });
      await loadPickles();
    } catch(e) {
      alert("Erro ao gerar pickles: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const carregarDadosCSV = async () => {
    setLoading(true);
    setLoadingMsg('Carregando CSV...');
    try {
      const resp = await apiCall("executar_carrega_dados", { username: user, password: pass });
      if (resp.erro) throw new Error(resp.erro);
      alert("✅ " + resp.mensagem);
      abrirModalCSV();
    } catch(e) {
      alert("Erro ao carregar dados: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const abrirModalCSV = async () => {
    setCsvModalOpen(true);
    try {
      const lista = await apiCall('listar_csv');
      setCsvList(lista || []);
    } catch(e) {
      alert("Erro ao listar CSV");
    }
  };

  const baixarSelecionadosCSV = async () => {
    const arquivos = Object.keys(selectedCsvs).filter(k => selectedCsvs[k]);
    if (arquivos.length === 0) return alert("Selecione pelo menos um arquivo.");
    try {
      const resp = await apiCall('baixar_zip_csv', { arquivos });
      if (resp.erro) throw new Error(resp.erro);
      window.open(resp.url, '_blank');
    } catch(e) {
      alert("Erro ao baixar: " + e.message);
    }
  };

  const excluirSelecionadosCSV = async () => {
    const arquivos = Object.keys(selectedCsvs).filter(k => selectedCsvs[k]);
    if (arquivos.length === 0) return alert("Selecione pelo menos um arquivo.");
    if (!window.confirm(`Deseja excluir ${arquivos.length} arquivo(s)?`)) return;
    try {
      const resp = await apiCall('excluir_csv', { arquivos });
      if (resp.erro) throw new Error(resp.erro);
      abrirModalCSV(); // recarregar
    } catch(e) {
      alert("Erro ao excluir: " + e.message);
    }
  };

  return (
    <div className="min-h-screen bg-bg-main flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-card p-xl w-full max-w-2xl animate-fade-in relative">
        {loading && (
          <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center z-50 rounded-lg">
             <div className="w-12 h-12 border-4 border-white/30 border-t-primary rounded-full animate-spin"></div>
             <p className="text-white mt-4 text-lg">{loadingMsg}</p>
          </div>
        )}
        
        <h2 className="text-2xl font-bold text-center text-text-main mb-lg">Análise de Compras</h2>
        
        <div className="space-y-md">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Usuário:</label>
            <input className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:border-primary" value={user} onChange={e => setUser(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Senha:</label>
            <input type="password" className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:border-primary" value={pass} onChange={e => setPass(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">Análise:</label>
            <select className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:border-primary" value={analiseSelecionada} onChange={e => setAnaliseSelecionada(e.target.value)}>
              {analises.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          
          <div className="flex flex-col gap-2 pt-4">
            <button onClick={executarAnalise} className="bg-primary hover:bg-primary-light text-white font-bold py-3 rounded-md shadow-sm transition-colors">Executar Análise (Nova)</button>
            <button onClick={onAnalysisReady} className="bg-surface-card border border-border text-text-main hover:bg-row-alt font-bold py-2 rounded-md shadow-sm transition-colors">Ir para Resultados (Sessão Ativa)</button>
            
            <div className="flex gap-2 mt-2">
              <button onClick={gerarDados} className="flex-1 border border-primary text-primary hover:bg-primary/10 font-semibold py-2 rounded-md transition-colors">Gerar Dados</button>
              <button onClick={carregarDadosCSV} className="flex-1 border border-primary text-primary hover:bg-primary/10 font-semibold py-2 rounded-md transition-colors">Carregar Dados CSV</button>
            </div>
            <button onClick={abrirModalCSV} className="bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 rounded-md transition-colors">Ver Arquivos CSV</button>
          </div>

          {pickles.length > 0 && (
             <div className="mt-4 border border-border rounded-lg overflow-hidden">
                <div className="bg-surface-canvas p-2 text-sm font-bold border-b border-border text-center">Arquivos Snapshots ({pickles.length})</div>
                <div className="max-h-48 overflow-y-auto">
                   <table className="w-full text-left text-xs">
                     <thead className="bg-primary text-white sticky top-0"><tr><th className="p-2">Nome</th><th className="p-2">Criação</th></tr></thead>
                     <tbody>
                       {pickles.map(p => (
                         <tr key={p.nome} className="border-b border-border"><td className="p-2 break-all">{p.nome}</td><td className="p-2 font-mono">{p.data_criacao}</td></tr>
                       ))}
                     </tbody>
                   </table>
                </div>
             </div>
          )}
        </div>
      </div>

      {csvModalOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white w-[800px] max-w-full rounded-lg shadow-2xl flex flex-col max-h-[90vh]">
            <div className="p-4 border-b flex justify-between items-center bg-gray-50 rounded-t-lg">
              <h3 className="font-bold text-lg">📂 Arquivos CSV Gerados</h3>
              <button onClick={() => setCsvModalOpen(false)} className="text-gray-500 hover:text-black font-bold text-xl">&times;</button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              <table className="w-full text-left text-sm border-collapse">
                <thead>
                  <tr className="border-b">
                     <th className="p-2 text-center"><input type="checkbox" onChange={e => {
                        const all = {};
                        csvList.forEach(c => all[c.nome] = e.target.checked);
                        setSelectedCsvs(all);
                     }} /></th>
                     <th className="p-2">Nome</th><th className="p-2">Tamanho</th><th className="p-2">Data</th><th className="p-2">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {csvList.map(c => (
                    <tr key={c.nome} className="border-b">
                      <td className="p-2 text-center"><input type="checkbox" checked={!!selectedCsvs[c.nome]} onChange={e => setSelectedCsvs({...selectedCsvs, [c.nome]: e.target.checked})} /></td>
                      <td className="p-2">{c.nome}</td><td className="p-2">{c.tamanho}</td><td className="p-2">{c.data_criacao}</td>
                      <td className="p-2"><a href={c.url} target="_blank" className="bg-primary text-white px-3 py-1 rounded text-xs no-underline">Download</a></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="p-4 border-t flex justify-between bg-gray-50 rounded-b-lg">
              <div className="gap-2 flex">
                <button onClick={baixarSelecionadosCSV} className="bg-gray-800 text-white px-4 py-2 rounded">⬇ Baixar Selecionados</button>
                <button onClick={excluirSelecionadosCSV} className="bg-status-danger text-white px-4 py-2 rounded">🗑 Excluir Selecionados</button>
              </div>
              <button onClick={() => setCsvModalOpen(false)} className="border px-4 py-2 rounded bg-white">Fechar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
