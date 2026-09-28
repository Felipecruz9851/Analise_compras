import React, { useState, useEffect, useCallback } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";
import MetricsCards from "./MetricsCards";
import PurchaseTable from "./PurchaseTable";
import { apiCall } from "../services/api";

function Dashboard() {
  const [data, setData] = useState([]);
  const [resumo, setResumo] = useState({});
  const [edicoes, setEdicoes] = useState({});
  const [totalGeral, setTotalGeral] = useState(0);
  const [totalItens, setTotalItens] = useState(0);

  const [startIndex, setStartIndex] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  const [filtros, setFiltros] = useState({});
  const [ordenacao, setOrdenacao] = useState({ coluna: null, direcao: "asc" });
  const [apenasEditados, setApenasEditados] = useState(false);
  const [apenasOcsProntas, setApenasOcsProntas] = useState(false);
  const [totalOcsProntas, setTotalOcsProntas] = useState(0);
  const [analiseNome, setAnaliseNome] = useState("");

  const getFiltrosTratados = (filtrosBrutos) => {
    const cleanFiltros = {};
    const colunasExatas = {};
    const colunasInvertidas = {};

    for (const [col, val] of Object.entries(filtrosBrutos)) {
      if (!val) continue;
      let cleanVal = val.trim();

      if (cleanVal.startsWith("==")) {
        colunasExatas[col] = true;
        cleanVal = cleanVal.substring(2).trim();
      } else if (cleanVal.startsWith("!==")) {
        colunasInvertidas[col] = true;
        colunasExatas[col] = true;
        cleanVal = cleanVal.substring(3).trim();
      } else if (cleanVal.startsWith("!=")) {
        colunasInvertidas[col] = true;
        cleanVal = cleanVal.substring(2).trim();
      }

      cleanFiltros[col] = cleanVal;
    }

    return { cleanFiltros, colunasExatas, colunasInvertidas };
  };

  const loadData = useCallback(
    async (
      reset = false,
      currentFiltros = filtros,
      currentOrdenacao = ordenacao,
      currentApenasEditados = apenasEditados,
      currentApenasOcsProntas = apenasOcsProntas,
    ) => {
      if (loading || (!hasMore && !reset)) return;
      setLoading(true);

      const currentStart = reset ? 0 : startIndex;
      const PAGE_SIZE = 50;

      const { cleanFiltros, colunasExatas, colunasInvertidas } =
        getFiltrosTratados(currentFiltros);

      try {
        const resp = await apiCall("obter_slice", {
          start: currentStart,
          size: PAGE_SIZE,
          filtros: cleanFiltros,
          ordenacao: currentOrdenacao,
          apenasEditados: currentApenasEditados,
          apenasOcsProntas: currentApenasOcsProntas,
          correspondenciaExata: false,
          filtrosInvertidos: false,
          colunasInvertidas: colunasInvertidas,
          colunasExatas: colunasExatas,
          data_ini: null,
          data_fim: null,
        });

        if (!resp || !resp.data || resp.data.length === 0) {
          setHasMore(false);
          if (reset) {
            setData([]);
            setTotalItens(0);
          }
        } else {
          if (resp.resumo && currentStart === 0) {
            setResumo(resp.resumo);
            setTotalGeral(resp.total_geral);
            if (resp.total_ocs_prontas !== undefined) {
              setTotalOcsProntas(resp.total_ocs_prontas);
            }
            if (resp.analise_nome) {
              setAnaliseNome(resp.analise_nome);
            }
          }
          setEdicoes(resp.edicoes || {});
          setData((prev) => (reset ? resp.data : [...prev, ...resp.data]));
          setStartIndex(currentStart + PAGE_SIZE);
          setTotalItens(resp.total);
          setHasMore(resp.data.length === PAGE_SIZE);
        }
      } catch (e) {
        console.error(e);
        setHasMore(false);
      } finally {
        setLoading(false);
      }
    },
    [
      startIndex,
      loading,
      hasMore,
      filtros,
      ordenacao,
      apenasEditados,
      apenasOcsProntas,
    ],
  );

  useEffect(() => {
    loadData(true);
  }, []);

  const handleFilter = (novosFiltros) => {
    setFiltros(novosFiltros);
    // Removemos a chamada direta aqui usando estados antigos e passamos os novos estados
    // Mas wait, loadData usa o estado loading! Se loading=true, ele retorna cedo!
    loadData(true, novosFiltros, ordenacao, apenasEditados, apenasOcsProntas);
  };

  const handleSort = (novaOrdenacao) => {
    setOrdenacao(novaOrdenacao);
    loadData(true, filtros, novaOrdenacao, apenasEditados, apenasOcsProntas);
  };

  const toggleFilterEdicoes = () => {
    const nextApenasEditados = !apenasEditados;
    setApenasEditados(nextApenasEditados);
    loadData(true, filtros, ordenacao, nextApenasEditados, apenasOcsProntas);
  };

  const toggleFilterOcs = () => {
    const nextApenasOcsProntas = !apenasOcsProntas;
    setApenasOcsProntas(nextApenasOcsProntas);
    loadData(true, filtros, ordenacao, apenasEditados, nextApenasOcsProntas);
  };

  const handleSaveEdition = async (rowId, valor) => {
    try {
      await apiCall("salvar_edicao", { rowId, valor });
      setEdicoes((prev) => {
        const next = { ...prev };
        if (valor === null || valor === undefined) {
          delete next[rowId];
        } else {
          next[rowId] = valor;
        }
        return next;
      });
      loadData(true);
    } catch (e) {
      console.error("Erro ao salvar edicao", e);
    }
  };

  const { cleanFiltros, colunasExatas, colunasInvertidas } =
    getFiltrosTratados(filtros);
  const filtrosPayload = {
    filtros: cleanFiltros,
    ordenacao,
    apenasEditados,
    apenasOcsProntas,
    correspondenciaExata: false,
    filtrosInvertidos: false,
    colunasInvertidas,
    colunasExatas,
  };

  const hasFilters =
    Object.keys(filtros).length > 0 || apenasEditados || apenasOcsProntas;

  const handleClearAllFilters = () => {
    setFiltros({});
    setApenasEditados(false);
    setApenasOcsProntas(false);
    loadData(true, {}, ordenacao, false, false);
  };

  return (
    <div className="bg-surface-canvas text-on-surface font-body h-screen overflow-hidden">
      <Sidebar resumo={resumo} totalGeral={totalGeral} />
      <div className="pl-72 flex flex-col h-screen">
        <Header
          totalItens={totalItens}
          analiseNome={analiseNome}
          filtrosPayload={filtrosPayload}
          hasFilters={hasFilters}
          onClearFilters={handleClearAllFilters}
        />
        <main className="w-full pt-20 bg-surface-canvas flex-1 flex flex-col min-h-0">
          <div className="p-lg flex flex-col gap-8 max-w-[1720px] mx-auto w-full flex-1 min-h-0 relative">
            <div className="flex-none">
              <MetricsCards
                totalGeral={totalGeral}
                totalItens={totalItens}
                edicoesCount={Object.keys(edicoes).length}
                isFilteredEdicoes={apenasEditados}
                onFilterEdicoes={toggleFilterEdicoes}
                totalOcsProntas={totalOcsProntas}
                isFilteredOcs={apenasOcsProntas}
                onFilterOcs={toggleFilterOcs}
              />
            </div>

            <div className="flex-1 min-h-0 bg-surface-card rounded-lg shadow-card overflow-hidden">
              <PurchaseTable
                data={data}
                edicoes={edicoes}
                onLoadMore={() => loadData(false)}
                hasMore={hasMore}
                onSaveEdition={handleSaveEdition}
                loading={loading}
                filtros={filtros}
                ordenacao={ordenacao}
                onFilter={handleFilter}
                onSort={handleSort}
              />
            </div>

            <div className="absolute bottom-2 right-10 flex items-end justify-end group z-30">
              <div className="w-8 h-8 rounded-full bg-surface-card border border-border shadow-sm flex items-center justify-center text-text-secondary cursor-help hover:bg-gray-50 transition-colors">
                <span className="material-symbols-outlined text-[18px]">
                  info
                </span>
              </div>

              <div className="absolute bottom-0 right-10 bg-surface-card rounded-lg shadow-xl border border-border px-4 py-2 flex items-center justify-end gap-4 text-[11px] text-text-secondary opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap mr-2 pointer-events-none">
                <strong>Filtros:</strong>
                <span>
                  <code className="bg-black/5 px-1 rounded">==</code> exato
                </span>
                <span>
                  <code className="bg-black/5 px-1 rounded">!=</code> não contém
                </span>
                <span>
                  <code className="bg-black/5 px-1 rounded">!==</code> dif.
                  exato
                </span>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
