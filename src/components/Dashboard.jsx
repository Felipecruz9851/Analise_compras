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
  const [analiseNome, setAnaliseNome] = useState('');

  const loadData = useCallback(
    async (reset = false, currentFiltros = filtros, currentOrdenacao = ordenacao, currentApenasEditados = apenasEditados, currentApenasOcsProntas = apenasOcsProntas) => {
      if (loading || (!hasMore && !reset)) return;
      setLoading(true);

      const currentStart = reset ? 0 : startIndex;
      const PAGE_SIZE = 50;

      try {
        const resp = await apiCall("obter_slice", {
          start: currentStart,
          size: PAGE_SIZE,
          filtros: currentFiltros,
          ordenacao: currentOrdenacao,
          apenasEditados: currentApenasEditados,
          apenasOcsProntas: currentApenasOcsProntas,
          correspondenciaExata: false,
          filtrosInvertidos: false,
          colunasInvertidas: {},
          colunasExatas: {},
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
    [startIndex, loading, hasMore, filtros, ordenacao, apenasEditados, apenasOcsProntas],
  );

  useEffect(() => {
    loadData(true);
  }, []);

  const handleFilter = (novosFiltros) => {
    setFiltros(novosFiltros);
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
      // Recarrega do zero para atualizar totais
      loadData(true);
    } catch (e) {
      console.error("Erro ao salvar edição", e);
    }
  };

  return (
    <div className="bg-surface-canvas text-on-surface font-body min-h-screen">
      <Sidebar resumo={resumo} totalGeral={totalGeral} />
      <div className="pl-72 flex flex-col min-h-screen">
        <Header totalItens={totalItens} analiseNome={analiseNome} />
        <main className="w-full pt-20 bg-surface-canvas flex-1">
          <div className="flex flex-col w-full">
            <div className="p-lg space-y-xl max-w-[1720px] mx-auto w-full">
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

              <div className="grid grid-cols-1 xl:grid-cols-12 gap-md items-start mt-8">
                {/* Table */}
                <div className="xl:col-span-12 bg-surface-card rounded-lg shadow-card">
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
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default Dashboard;
