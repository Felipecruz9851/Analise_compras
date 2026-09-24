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

  const loadData = useCallback(
    async (reset = false) => {
      if (loading || (!hasMore && !reset)) return;
      setLoading(true);

      const currentStart = reset ? 0 : startIndex;
      const PAGE_SIZE = 50;

      try {
        const resp = await apiCall("obter_slice", {
          start: currentStart,
          size: PAGE_SIZE,
          filtros: {},
          ordenacao: { coluna: null, direcao: "asc" },
          correspondenciaExata: false,
          filtrosInvertidos: false,
          colunasInvertidas: {},
          colunasExatas: {},
          data_ini: null,
          data_fim: null,
        });

        if (!resp || !resp.data || resp.data.length === 0) {
          setHasMore(false);
        } else {
          if (resp.resumo && currentStart === 0) {
            setResumo(resp.resumo);
            setTotalGeral(resp.total_geral);
          }
          setEdicoes((prev) => ({ ...prev, ...(resp.edicoes || {}) }));
          setData((prev) => (reset ? resp.data : [...prev, ...resp.data]));
          setStartIndex(currentStart + PAGE_SIZE);
          setTotalItens(resp.total);
        }
      } catch (e) {
        console.error(e);
        setHasMore(false);
      } finally {
        setLoading(false);
      }
    },
    [startIndex, loading, hasMore],
  );

  useEffect(() => {
    loadData(true);
  }, []);

  const handleSaveEdition = async (rowId, valor) => {
    try {
      await apiCall("salvar_edicao", { rowId, valor });
      setEdicoes((prev) => ({ ...prev, [rowId]: valor }));
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
        <Header totalItens={totalItens} />
        <main className="w-full pt-20 bg-surface-canvas flex-1">
          <div className="flex flex-col w-full">
            <div className="p-lg space-y-xl max-w-[1720px] mx-auto w-full">
              <MetricsCards
                totalGeral={totalGeral}
                totalItens={totalItens}
                edicoesCount={Object.keys(edicoes).length}
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
