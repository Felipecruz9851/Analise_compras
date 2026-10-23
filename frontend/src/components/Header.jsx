import React, { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { apiCall } from "../services/api";
import logoLider from "../logo_lider.png";

export default function Header({
  totalItens,
  analiseNome,
  filtrosPayload,
  hasFilters,
  onClearFilters,
  sidebarOpen = true,
  onToggleSidebar,
  showMetrics = true,
  onToggleMetrics,
  has30d = false,
  edicoesCount = 0,
  onAplicar30dEmMassa,
  onRestaurarTodasEdicoes,
}) {
  const [loading, setLoading] = useState(false);
  const [exportsModalOpen, setExportsModalOpen] = useState(false);
  const [exportsList, setExportsList] = useState([]);
  const [selectedExports, setSelectedExports] = useState({});
  const [ocsMenuOpen, setOcsMenuOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOcsMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

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

  const handleGerarCsvVisivel = async () => {
    try {
      setLoading(true);
      await apiCall("gerar_csv_visivel", filtrosPayload);
      alert("CSV gerado com sucesso!");
    } catch (e) {
      alert("Erro ao gerar CSV: " + e.message);
    } finally {
      setLoading(false);
    }
  };

  const abrirExports = async () => {
    setExportsModalOpen(true);
    try {
      const lista = await apiCall("listar_exports");
      setExportsList(lista || []);
    } catch (e) {
      alert("Erro ao listar exportações: " + e.message);
    }
  };

  const baixarSelecionados = async () => {
    const arquivos = Object.keys(selectedExports).filter(
      (k) => selectedExports[k],
    );
    if (arquivos.length === 0) return alert("Selecione pelo menos um arquivo.");
    try {
      const resp = await apiCall("baixar_zip", { arquivos });
      if (resp.erro) throw new Error(resp.erro);
      const a = document.createElement("a");
      a.href = resp.url;
      a.download = resp.url.split("/").pop();
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (e) {
      alert("Erro ao baixar: " + e.message);
    }
  };

  const excluirSelecionados = async () => {
    const arquivos = Object.keys(selectedExports).filter(
      (k) => selectedExports[k],
    );
    if (arquivos.length === 0) return alert("Selecione pelo menos um arquivo.");
    if (!window.confirm(`Deseja excluir ${arquivos.length} arquivo(s)?`))
      return;
    try {
      const resp = await apiCall("excluir_exports", { arquivos });
      if (resp.erro) throw new Error(resp.erro);
      abrirExports();
    } catch (e) {
      alert("Erro ao excluir: " + e.message);
    }
  };

  return (
    <header
      className={`fixed top-0 right-0 h-14 bg-surface-card/95 backdrop-blur-xl z-40 border-b border-border shadow-sm px-4 flex items-center justify-between transition-all duration-300 ease-in-out ${
        sidebarOpen ? "left-72" : "left-0"
      }`}
    >
      {/* Canto superior esquerdo: Botão de toggle e Logo Líder (quando sidebar oculta) */}
      <div className="flex items-center gap-2.5 shrink-0 z-10">
        <button
          onClick={onToggleSidebar}
          className="p-1.5 rounded-lg text-text-secondary hover:text-text-main hover:bg-black/5 transition-colors flex items-center justify-center shrink-0"
          title={sidebarOpen ? "Ocultar barra lateral" : "Exibir barra lateral"}
          type="button"
        >
          <span className="material-symbols-outlined text-[22px]">
            {sidebarOpen ? "dock_to_left" : "menu"}
          </span>
        </button>

        {!sidebarOpen && (
          <img
            src={logoLider}
            alt="Logo Líder"
            className="max-h-8 w-auto shrink-0"
          />
        )}
      </div>

      {/* Título da página centralizado */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center justify-center gap-2 pointer-events-none max-w-[35%] xl:max-w-[48%] text-center">
        <h2
          className="text-base font-bold text-text-main truncate pointer-events-auto"
          title={`Análise de matéria prima - ${analiseNome || "Carregando..."}`}
        >
          Análise de matéria prima - {analiseNome || "Carregando..."}
        </h2>
      </div>

      {/* Canto direito: controles e ações */}
      <div className="flex items-center gap-2.5 shrink-0 z-10 ml-auto">
        <span className="text-xs text-text-secondary flex items-center gap-1">
          <span>Registros:</span>
          <span className="font-bold text-primary">{totalItens}</span>
        </span>

        {onToggleMetrics && (
          <button
            onClick={onToggleMetrics}
            className={`text-xs font-semibold px-2 py-1 rounded-lg border transition-colors flex items-center gap-1 ${
              showMetrics
                ? "bg-primary/10 border-primary/30 text-primary"
                : "border-border text-text-secondary hover:bg-black/5"
            }`}
            title={
              showMetrics
                ? "Ocultar cartões de resumo"
                : "Exibir cartões de resumo"
            }
            type="button"
          >
            <span className="material-symbols-outlined text-[15px]">
              {showMetrics ? "visibility" : "visibility_off"}
            </span>
            <span>Métricas</span>
          </button>
        )}

        {hasFilters && (
          <button
            onClick={onClearFilters}
            className="text-text-secondary hover:text-error text-xs font-semibold transition-colors flex items-center gap-1 bg-transparent px-2 py-1 rounded-lg hover:bg-error/10"
            title="Limpar todos os filtros"
            type="button"
          >
            <span className="material-symbols-outlined text-[15px]">
              filter_alt_off
            </span>
            Limpar Filtros
          </button>
        )}

        {totalItens > 0 && has30d && onAplicar30dEmMassa && (
          <button
            onClick={onAplicar30dEmMassa}
            disabled={loading}
            className="bg-slate-800 hover:bg-slate-900 text-white px-2.5 py-1.5 rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1"
            title="Aplicar a sugestão de cálculo de 30 dias em todas as decisões de compra"
            type="button"
          >
            <span className="material-symbols-outlined text-[15px]">bolt</span>
            <span>Aplicar 30d</span>
          </button>
        )}

        {totalItens > 0 && edicoesCount > 0 && onRestaurarTodasEdicoes && (
          <button
            onClick={onRestaurarTodasEdicoes}
            disabled={loading}
            className="border border-border text-text-secondary hover:text-error hover:border-error/40 px-2.5 py-1.5 rounded-lg text-xs font-semibold shadow-xs transition-colors flex items-center gap-1"
            title={`Restaurar ${edicoesCount} decisões para o cálculo base original`}
            type="button"
          >
            <span className="material-symbols-outlined text-[15px]">undo</span>
            <span>Restaurar ({edicoesCount})</span>
          </button>
        )}

        {totalItens > 0 && (
          <>
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setOcsMenuOpen(!ocsMenuOpen)}
                disabled={loading}
                className="bg-primary hover:bg-primary-light text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm disabled:opacity-50 transition-colors flex items-center gap-1"
                type="button"
              >
                {loading ? "Processando..." : "Gerar OCs"}
                <span className="material-symbols-outlined text-[15px]">
                  expand_more
                </span>
              </button>
              {ocsMenuOpen && (
                <div className="absolute top-full right-0 mt-1 w-56 bg-white border border-border rounded-lg shadow-xl z-50 py-1 text-xs text-text-main">
                  <button
                    onClick={() => {
                      setOcsMenuOpen(false);
                      handleGerarOCs();
                    }}
                    className="w-full text-left px-3.5 py-2 hover:bg-bg-main transition-colors font-medium"
                  >
                    Executar normalmente
                  </button>
                  <button
                    onClick={() => {
                      setOcsMenuOpen(false);
                      handleGerarCsvVisivel();
                    }}
                    className="w-full text-left px-3.5 py-2 hover:bg-bg-main transition-colors font-medium"
                  >
                    Gerar CSV apenas visível
                  </button>
                </div>
              )}
            </div>
            <button
              onClick={abrirExports}
              className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1.5 rounded-lg text-xs font-semibold shadow-sm transition-colors"
              type="button"
            >
              Exportações
            </button>
          </>
        )}
      </div>

      {exportsModalOpen &&
        createPortal(
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-[9999]">
            <div className="bg-white w-[800px] max-w-full rounded-lg shadow-2xl flex flex-col max-h-[90vh] mx-4">
              <div className="p-4 border-b flex justify-between items-center bg-gray-50 rounded-t-lg">
                <h3 className="font-bold text-lg">📁 Exportações Geradas</h3>
                <button
                  onClick={() => setExportsModalOpen(false)}
                  className="text-gray-500 hover:text-black font-bold text-xl"
                >
                  &times;
                </button>
              </div>
              <div className="p-4 overflow-y-auto flex-1 min-h-[300px]">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="border-b">
                      <th className="p-2 text-center w-10">
                        <input
                          type="checkbox"
                          onChange={(e) => {
                            const all = {};
                            exportsList.forEach(
                              (c) => (all[c.nome] = e.target.checked),
                            );
                            setSelectedExports(all);
                          }}
                        />
                      </th>
                      <th className="p-2">Nome</th>
                      <th className="p-2">Tamanho</th>
                      <th className="p-2">Data</th>
                      <th className="p-2 text-center">Ação</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exportsList.length === 0 && (
                      <tr>
                        <td
                          colSpan="5"
                          className="p-4 text-center text-gray-500"
                        >
                          Nenhum arquivo encontrado.
                        </td>
                      </tr>
                    )}
                    {exportsList.map((c) => (
                      <tr key={c.nome} className="border-b hover:bg-gray-50">
                        <td className="p-2 text-center">
                          <input
                            type="checkbox"
                            checked={!!selectedExports[c.nome]}
                            onChange={(e) =>
                              setSelectedExports({
                                ...selectedExports,
                                [c.nome]: e.target.checked,
                              })
                            }
                          />
                        </td>
                        <td className="p-2">{c.nome}</td>
                        <td className="p-2">{c.tamanho}</td>
                        <td className="p-2">{c.data_criacao}</td>
                        <td className="p-2 text-center">
                          <a
                            href={c.url}
                            download={c.nome}
                            className="bg-primary hover:bg-primary-light text-white px-3 py-1 rounded text-xs no-underline transition-colors"
                          >
                            Download
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="p-4 border-t flex justify-between bg-gray-50 rounded-b-lg">
                <div className="gap-2 flex">
                  <button
                    onClick={baixarSelecionados}
                    className="bg-gray-800 hover:bg-gray-900 text-white px-4 py-2 rounded transition-colors font-semibold text-sm"
                  >
                    ⬇ Baixar Selecionados
                  </button>
                  <button
                    onClick={excluirSelecionados}
                    className="bg-status-danger hover:bg-red-700 text-white px-4 py-2 rounded transition-colors font-semibold text-sm"
                  >
                    🗑 Excluir Selecionados
                  </button>
                </div>
                <button
                  onClick={() => setExportsModalOpen(false)}
                  className="border px-4 py-2 rounded bg-white hover:bg-gray-100 font-semibold text-sm transition-colors"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>,
          document.body,
        )}
    </header>
  );
}
