import React, { useEffect, useRef } from "react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement);

function ehColunaMes(col) {
  return /^\d{4}-\d{2}$/.test(col);
}

const parseNumeroBR = (valor) => {
  if (!valor) return 0;
  const str = valor.toString().trim();
  const lastCommaIndex = str.lastIndexOf(",");
  const lastDotIndex = str.lastIndexOf(".");
  if (lastCommaIndex > lastDotIndex) {
    return parseFloat(str.replace(/\./g, "").replace(",", ".")) || 0;
  }
  return parseFloat(str) || 0;
};

const valueLabelsPlugin = {
  id: "valueLabels",
  afterDatasetsDraw(chart, args, options) {
    const { ctx } = chart;
    ctx.save();
    ctx.font = "10px Arial";
    ctx.fillStyle = "#1976d2";
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";

    chart.data.datasets.forEach((dataset, i) => {
      const meta = chart.getDatasetMeta(i);
      meta.data.forEach((element, index) => {
        const dataPoint = dataset.data[index];
        // Formata o número se for grande (ex: 1.2k) ou apenas mostra inteiro
        const text = Number.isInteger(dataPoint)
          ? dataPoint
          : parseFloat(dataPoint).toFixed(1);
        ctx.fillText(text, element.x, element.y - 4);
      });
    });
    ctx.restore();
  },
};

const Sparkline = ({ labels, data }) => {
  const chartData = {
    labels: labels.slice(0, -1),
    datasets: [
      {
        data: data.slice(0, -1),
        borderColor: "#1976d2",
        borderWidth: 1.5,
        pointRadius: 3,
        tension: 0.3,
      },
    ],
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { top: 25, bottom: 8, left: 15, right: 15 } },
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { display: false },
      y: { display: false, grace: "20%" },
    },
  };
  return (
    <div style={{ width: 250, height: 120 }}>
      <Line data={chartData} options={options} plugins={[valueLabelsPlugin]} />
    </div>
  );
};

export default function PurchaseTable({
  data,
  edicoes,
  onLoadMore,
  hasMore,
  onSaveEdition,
  loading,
}) {
  const sentinelRef = useRef(null);

  useEffect(() => {
    if (!sentinelRef.current) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore) {
          onLoadMore();
        }
      },
      { threshold: 0.1 },
    );
    observer.observe(sentinelRef.current);
    return () => observer.disconnect();
  }, [onLoadMore, hasMore]);

  if (!data || data.length === 0)
    return <div className="p-4 text-center">Carregando...</div>;

  const todasColunas = Object.keys(data[0]).filter((c) => c !== "__rowId");
  const colunasMes = todasColunas.filter(ehColunaMes).sort();
  const colunasTabela = todasColunas.filter(
    (c) => !ehColunaMes(c) && c !== "Gráfico",
  );
  colunasTabela.splice(2, 0, "Gráfico");

  return (
    <div className="w-full overflow-x-auto max-h-[800px] overflow-y-auto relative">
      <table className="w-full text-left border-collapse whitespace-nowrap">
        <thead className="bg-bg-main text-text-secondary text-xs uppercase tracking-wider sticky top-0 z-10 shadow-sm">
          <tr>
            <th className="py-2.5 px-3 w-10 text-center border-b border-border">
              <input type="checkbox" className="accent-primary" />
            </th>
            {colunasTabela.map((col) => (
              <th
                key={col}
                className={`py-2.5 px-3 font-semibold border-b border-border ${col === "Decis Compras" || col === "Valor Comprado" ? "bg-cell-highlight-bg text-cell-highlight-text" : ""}`}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border text-sm text-text-main">
          {data.map((linha) => {
            const rowId = linha.__rowId;
            const foiEditado = edicoes[rowId] !== undefined;
            const bgClass = foiEditado
              ? "bg-cell-edited-bg/50"
              : "hover:bg-row-alt";

            return (
              <tr key={rowId} className={`transition-colors ${bgClass}`}>
                <td className="py-2 px-3 text-center">
                  <input type="checkbox" className="accent-primary" />
                </td>
                {colunasTabela.map((col) => {
                  if (col === "Gráfico") {
                    const valores = colunasMes.map((m) =>
                      parseNumeroBR(linha[m]),
                    );
                    return (
                      <td key={col} className="py-2 px-3">
                        <Sparkline labels={colunasMes} data={valores} />
                      </td>
                    );
                  }

                  if (col === "Decis Compras") {
                    const valorOriginal = parseNumeroBR(linha[col]);
                    const valorFinal = foiEditado
                      ? edicoes[rowId]
                      : valorOriginal;

                    return (
                      <td key={col} className="py-2 px-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <input
                            type="number"
                            defaultValue={valorFinal}
                            onBlur={(e) => {
                              const num = parseNumeroBR(e.target.value);
                              if (num !== valorOriginal) {
                                onSaveEdition(rowId, num);
                              } else if (foiEditado) {
                                onSaveEdition(rowId, null); // Reverte edição se voltar pro original
                              }
                            }}
                            className={`w-24 h-7 text-center font-bold rounded border px-1 ${foiEditado ? "border-cell-edited-border text-cell-edited-text bg-white" : "border-border"}`}
                          />
                          {foiEditado && (
                            <button
                              onClick={() => {
                                onSaveEdition(rowId, null);
                              }}
                              className="w-6 h-6 rounded-full bg-cell-edited-border text-white flex items-center justify-center shadow-sm"
                              title="Restaurar"
                            >
                              <span className="material-symbols-outlined text-[14px]">
                                undo
                              </span>
                            </button>
                          )}
                        </div>
                      </td>
                    );
                  }

                  let formatVal = linha[col] ?? "";
                  if (col === "Valor Comprado") {
                    // Caso a coluna tenha sido editada, podemos sobrescrever com o novo valor, mas o ideal é que a recarga do zero da API traga o valor comprado já atualizado do backend.
                    // O backend recalcula o valor comprado baseado nas edições no Python?
                    // Sim, se a API `salvar_edicao` faz isso e `obter_slice` pega o novo cálculo.
                    formatVal = parseNumeroBR(formatVal).toLocaleString(
                      "pt-BR",
                      { style: "currency", currency: "BRL" },
                    );
                  }

                  return (
                    <td
                      key={col}
                      className={`py-2 px-3 truncate max-w-[200px] ${col === "Valor Comprado" ? "font-bold text-right text-primary" : ""} ${foiEditado && col === "Valor Comprado" ? "!text-cell-edited-text" : ""}`}
                      title={linha[col]}
                    >
                      {formatVal}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <div
        ref={sentinelRef}
        className="h-10 w-full flex items-center justify-center"
      >
        {loading && (
          <span className="text-text-secondary text-sm">
            Carregando mais itens...
          </span>
        )}
      </div>
    </div>
  );
}
