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
    ctx.font = "bold 11px sans-serif";
    ctx.fillStyle = "#1565c0";
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
        borderWidth: 1,
        pointRadius: 3,
        tension: 0.2,
      },
    ],
  };
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    layout: { padding: { top: 5, bottom: -5, left: 0, right: 0 } },
    plugins: { legend: { display: false }, tooltip: { enabled: false } },
    scales: {
      x: { display: true },
      y: { display: false, grace: "30%" },
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
  filtros = {},
  ordenacao = { coluna: null, direcao: "asc" },
  onFilter,
  onSort,
}) {
  const sentinelRef = useRef(null);
  const [openMenuCol, setOpenMenuCol] = React.useState(null);
  const [localFilter, setLocalFilter] = React.useState("");

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

  // Handle closing menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setOpenMenuCol(null);
    if (openMenuCol) {
      document.addEventListener("click", handleClickOutside);
    }
    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  }, [openMenuCol]);

  if (!data || data.length === 0)
    return <div className="p-4 text-center">Carregando...</div>;

  const todasColunas = Object.keys(data[0]).filter((c) => c !== "__rowId");
  const colunasMes = todasColunas.filter(ehColunaMes).sort();
  const colunasTabela = todasColunas.filter(
    (c) => !ehColunaMes(c) && c !== "Gráfico",
  );
  colunasTabela.splice(2, 0, "Gráfico");

  return (
    <div className="w-full h-full overflow-x-auto overflow-y-auto relative">
      <table className="w-full text-left border-collapse whitespace-nowrap">
        <thead className="bg-bg-main text-text-secondary text-xs uppercase tracking-wider sticky top-0 z-10 shadow-sm">
          <tr>
            <th className="py-2.5 px-3 w-10 text-center border-b border-border">
              <input type="checkbox" className="accent-primary" />
            </th>
            {colunasTabela.map((col) => (
              <th
                key={col}
                className={`relative py-2.5 px-3 font-semibold border-b border-border hover:bg-black/5 cursor-pointer select-none transition-colors ${col === "Decis Compras" || col === "Valor Comprado" ? "bg-cell-highlight-bg text-cell-highlight-text" : ""}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (col === "Gráfico") return;
                  if (openMenuCol === col) {
                    setOpenMenuCol(null);
                  } else {
                    setOpenMenuCol(col);
                    setLocalFilter(filtros[col] || "");
                  }
                }}
              >
                <div className="flex items-center gap-1">
                  {col}
                  {ordenacao.coluna === col && (
                    <span className="material-symbols-outlined text-[14px]">
                      {ordenacao.direcao === "asc"
                        ? "arrow_upward"
                        : "arrow_downward"}
                    </span>
                  )}
                  {filtros[col] && (
                    <span className="material-symbols-outlined text-[14px] text-primary">
                      filter_alt
                    </span>
                  )}
                </div>

                {openMenuCol === col && col !== "Gráfico" && (
                  <div
                    className="absolute top-full left-0 mt-1 w-56 bg-white border border-border rounded-lg shadow-xl z-50 p-2 normal-case font-normal text-sm text-text-main"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="mb-2 text-xs font-semibold text-text-secondary uppercase">
                      Ordenar
                    </div>
                    <button
                      className={`w-full text-left px-2 py-1.5 rounded hover:bg-bg-main mb-1 flex items-center gap-2 ${ordenacao.coluna === col && ordenacao.direcao === "asc" ? "bg-primary/10 text-primary" : ""}`}
                      onClick={() => {
                        onSort({ coluna: col, direcao: "asc" });
                        setOpenMenuCol(null);
                      }}
                    >
                      <span className="material-symbols-outlined text-[16px]">
                        arrow_upward
                      </span>{" "}
                      Crescente
                    </button>
                    <button
                      className={`w-full text-left px-2 py-1.5 rounded hover:bg-bg-main mb-3 flex items-center gap-2 ${ordenacao.coluna === col && ordenacao.direcao === "desc" ? "bg-primary/10 text-primary" : ""}`}
                      onClick={() => {
                        onSort({ coluna: col, direcao: "desc" });
                        setOpenMenuCol(null);
                      }}
                    >
                      <span className="material-symbols-outlined text-[16px]">
                        arrow_downward
                      </span>{" "}
                      Decrescente
                    </button>

                    <div className="mb-2 text-xs font-semibold text-text-secondary uppercase">
                      Filtrar
                    </div>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        onFilter({ ...filtros, [col]: localFilter });
                        setOpenMenuCol(null);
                      }}
                      className="flex gap-2"
                    >
                      <input
                        type="text"
                        value={localFilter}
                        onChange={(e) => setLocalFilter(e.target.value)}
                        placeholder="Buscar..."
                        className="w-full bg-bg-main border border-border rounded px-2 py-1 text-sm focus:outline-none focus:border-primary"
                      />
                      <button
                        type="submit"
                        className="bg-primary text-white rounded px-2 flex items-center justify-center"
                      >
                        <span className="material-symbols-outlined text-[16px]">
                          search
                        </span>
                      </button>
                    </form>
                    {filtros[col] && (
                      <button
                        className="mt-2 w-full text-center text-xs text-error hover:underline"
                        onClick={() => {
                          const newFiltros = { ...filtros };
                          delete newFiltros[col];
                          onFilter(newFiltros);
                          setOpenMenuCol(null);
                        }}
                      >
                        Limpar Filtro
                      </button>
                    )}
                  </div>
                )}
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
                <td className="py-0.5 px-3 text-center">
                  <input type="checkbox" className="accent-primary" />
                </td>
                {colunasTabela.map((col) => {
                  if (col === "Gráfico") {
                    const valores = colunasMes.map((m) =>
                      parseNumeroBR(linha[m]),
                    );
                    return (
                      <td key={col} className="py-0.5 px-3">
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
                      <td key={col} className="py-0.5 px-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <input
                            key={`input-${rowId}-${foiEditado ? "editado" : "original"}-${valorFinal}`}
                            type="number"
                            defaultValue={valorFinal}
                            onBlur={(e) => {
                              const num = parseNumeroBR(e.target.value);
                              if (num !== valorFinal) {
                                // Só salva se o valor digitado for diferente do que já está no estado!
                                if (num === valorOriginal) {
                                  onSaveEdition(rowId, null);
                                } else {
                                  onSaveEdition(rowId, num);
                                }
                              }
                            }}
                            className={`w-24 h-6 text-sm text-center font-bold rounded border px-1 ${foiEditado ? "border-cell-edited-border text-cell-edited-text bg-white" : "border-border"}`}
                          />
                          {foiEditado && (
                            <button
                              onMouseDown={(e) => {
                                e.preventDefault();
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
                    formatVal = parseNumeroBR(formatVal).toLocaleString(
                      "pt-BR",
                      { style: "currency", currency: "BRL" },
                    );
                  }

                  if (
                    col === "Descrição" ||
                    col === "Den. Item" ||
                    col === "Descricao"
                  ) {
                    return (
                      <td
                        key={col}
                        className="py-0.5 px-3 align-middle"
                        title={linha[col]}
                      >
                        <div className="whitespace-normal min-w-[290px] max-w-[290px] line-clamp-3 text-sm">
                          {formatVal}
                        </div>
                      </td>
                    );
                  }

                  return (
                    <td
                      key={col}
                      className={`py-0.5 px-3 truncate max-w-[200px] ${col === "Valor Comprado" ? "font-bold text-right text-primary" : ""} ${foiEditado && col === "Valor Comprado" ? "!text-cell-edited-text" : ""}`}
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
