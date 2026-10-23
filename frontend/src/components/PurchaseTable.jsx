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

export function ehColunaCentralizada(col) {
  if (!col) return false;
  const base = col.replace(" (30d)", "").trim();
  // Colunas de texto longo explicativo permanecem alinhadas à esquerda
  if (
    base === "Descrição" ||
    base === "Descricao" ||
    base === "Den. Item" ||
    base === "Observação" ||
    base === "Observacao"
  ) {
    return false;
  }
  return base.length < 15;
}

export const parseNumeroBR = (valor) => {
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
  afterDatasetsDraw(chart, _args, _options) {
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
    labels: labels.slice(0, 5),
    datasets: [
      {
        data: data.slice(0, 5),
        borderColor: "#1976d2",
        borderWidth: 1,
        pointRadius: 3,
        tension: 0.3,
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
  const [colunasExpandidas30, setColunasExpandidas30] = React.useState({});

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

  if (!data || data.length === 0) {
    if (loading) return <div className="p-4 text-center">Carregando...</div>;
    return (
      <div className="p-4 text-center text-text-secondary">
        Nenhum registro encontrado.
      </div>
    );
  }

  const todasColunas = Object.keys(data[0]).filter((c) => c !== "__rowId");
  const colunasMes = todasColunas.filter(ehColunaMes).sort();

  // Detecta quais colunas possuem variante _N30 calculada
  const colunas30Disponiveis = new Set();
  todasColunas.forEach((c) => {
    if (c.endsWith("_N30")) {
      colunas30Disponiveis.add(c.replace(/_N30$/, ""));
    }
  });

  // Oculta as colunas brutas _N30 do fluxo padrão da tabela
  const colunasTabela = todasColunas.filter(
    (c) => !ehColunaMes(c) && !c.endsWith("_N30") && c !== "Gráfico",
  );
  colunasTabela.splice(2, 0, "Gráfico");

  // Monta a lista final intercalando as colunas companheiras expandidas
  const colunasFinais = [];
  for (const col of colunasTabela) {
    colunasFinais.push(col);
    if (colunasExpandidas30[col]) {
      colunasFinais.push(`${col} (30d)`);
    }
  }

  return (
    <div className="w-full h-full overflow-x-auto overflow-y-auto relative">
      <table className="w-full text-left border-collapse whitespace-nowrap">
        <thead className="bg-bg-main text-text-secondary text-xs uppercase tracking-wider sticky top-0 z-10 shadow-sm">
          <tr>
            <th className="py-2.5 px-3 w-10 text-center border-b border-border">
              <input type="checkbox" className="accent-primary" />
            </th>
            {colunasFinais.map((col) => {
              const is30Col = col.endsWith(" (30d)");
              const baseColName = is30Col ? col.replace(" (30d)", "") : col;
              const tem30 = colunas30Disponiveis.has(col);
              const isExpandida = !!colunasExpandidas30[col];

              const isCenter = ehColunaCentralizada(col);

              if (is30Col) {
                return (
                  <th
                    key={col}
                    className={`relative py-2.5 px-3 font-semibold border-b border-blue-200 bg-blue-50/90 text-blue-900 select-none shadow-xs ${
                      isCenter ? "text-center" : "text-left"
                    }`}
                  >
                    <div className={`flex items-center gap-1 ${isCenter ? "justify-center" : "justify-between"}`}>
                      <span className="flex items-center gap-1 font-bold text-xs text-blue-900" title={col}>
                        <span className="material-symbols-outlined text-[14px] text-blue-600">
                          history_toggle_off
                        </span>
                        {col}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setColunasExpandidas30((prev) => ({
                            ...prev,
                            [baseColName]: false,
                          }));
                        }}
                        className="text-blue-500 hover:text-red-500 p-0.5 rounded hover:bg-blue-100 transition-colors"
                        title="Fechar comparativo 30 dias"
                      >
                        <span className="material-symbols-outlined text-[14px]">close</span>
                      </button>
                    </div>
                  </th>
                );
              }

              return (
                <th
                  key={col}
                  className={`relative py-2.5 px-3 font-semibold border-b border-border hover:bg-black/5 cursor-pointer select-none transition-colors ${
                    isCenter ? "text-center" : "text-left"
                  } ${
                    col === "Decis Compras" || col === "Valor Comprado"
                      ? "bg-cell-highlight-bg text-cell-highlight-text"
                      : ""
                  }`}
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
                  <div className={`flex items-center gap-1 ${isCenter ? "justify-center" : "justify-between"}`}>
                    <div className={`flex items-center gap-1 ${isCenter ? "justify-center" : ""}`}>
                      <span>{col}</span>
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

                    {tem30 && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setColunasExpandidas30((prev) => ({
                            ...prev,
                            [col]: !prev[col],
                          }));
                        }}
                        className={`px-1.5 py-0.5 text-[10px] rounded font-bold transition-all ml-1 shrink-0 flex items-center gap-0.5 shadow-xs ${
                          isExpandida
                            ? "bg-blue-600 text-white"
                            : "bg-blue-100 text-blue-700 hover:bg-blue-200"
                        }`}
                        title={
                          isExpandida
                            ? "Recolher comparativo de 30 dias"
                            : "Exibir coluna comparativa de 30 dias lado a lado"
                        }
                      >
                        30d
                      </button>
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
            );
          })}
          </tr>
        </thead>
        <tbody className="divide-y divide-border text-sm text-text-main">
          {data.map((linha) => {
            const rowId = linha.__rowId;
            const foiEditado = edicoes[rowId] !== undefined || edicoes[String(rowId)] !== undefined;
            const bgClass = foiEditado
              ? "bg-cell-edited-bg/50"
              : "hover:bg-row-alt";

            return (
              <tr key={rowId} className={`transition-colors ${bgClass}`}>
                <td className="py-0.5 px-3 text-center">
                  <input type="checkbox" className="accent-primary" />
                </td>
                {colunasFinais.map((col) => {
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

                  const is30Col = col.endsWith(" (30d)");
                  if (is30Col) {
                    const baseCol = col.replace(" (30d)", "");
                    const chave30 = `${baseCol}_N30`;
                    let val30 = linha[chave30] ?? "";
                    const isCurrency =
                      baseCol === "Valor Comprado" || baseCol === "Valor Estoque" || baseCol === "Valor Unitário";

                    if (isCurrency && val30 !== "") {
                      val30 = parseNumeroBR(val30).toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                        minimumFractionDigits: 3,
                        maximumFractionDigits: 3,
                      });
                    } else if (typeof val30 === "number" || (typeof val30 === "string" && val30.trim() !== "" && !isNaN(Number(val30.replace(",", "."))))) {
                      const num = parseNumeroBR(val30);
                      val30 = num.toLocaleString("pt-BR", {
                        minimumFractionDigits: 3,
                        maximumFractionDigits: 3,
                      });
                    }

                    if (baseCol === "Decis Compras") {
                      const num30 = parseNumeroBR(linha[chave30]);
                      const valorAtual = foiEditado
                        ? edicoes[rowId]
                        : parseNumeroBR(linha["Decis Compras"]);

                      return (
                        <td
                          key={col}
                          className="py-1 px-3 text-center bg-blue-50/50 text-blue-900 font-bold border-l border-blue-200/60"
                        >
                          <div className="flex items-center justify-center gap-1.5">
                            <span className="font-mono text-sm">{num30.toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}</span>
                            {Math.abs(num30 - valorAtual) > 0.0001 && (
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onSaveEdition(rowId, num30);
                                }}
                                className="px-1.5 py-0.5 bg-blue-600 hover:bg-blue-700 text-white rounded text-[10px] font-bold flex items-center gap-0.5 shadow-xs transition-colors"
                                title={`Copiar ${num30} para Decisão de Compra`}
                              >
                                <span className="material-symbols-outlined text-[12px]">
                                  bolt
                                </span>
                                Aplicar
                              </button>
                            )}
                          </div>
                        </td>
                      );
                    }

                    return (
                      <td
                        key={col}
                        className={`py-1 px-3 bg-blue-50/30 text-blue-950 font-medium truncate max-w-[200px] border-l border-blue-100 ${
                          isCenter
                            ? "text-center"
                            : isCurrency
                              ? "text-right font-bold text-blue-800"
                              : "text-left"
                        }`}
                        title={String(linha[chave30] ?? "")}
                      >
                        {val30}
                      </td>
                    );
                  }

                  if (col === "Decis Compras") {
                    const valorOriginal = parseNumeroBR(linha[col]);
                    const valorFinal = foiEditado
                      ? parseNumeroBR(edicoes[rowId] ?? edicoes[String(rowId)])
                      : valorOriginal;

                    const tem30 =
                      linha["Decis Compras_N30"] !== undefined &&
                      linha["Decis Compras_N30"] !== null;
                    const val30 = tem30
                      ? parseNumeroBR(linha["Decis Compras_N30"])
                      : null;

                    return (
                      <td key={col} className="py-0.5 px-3 text-center">
                        <div className="flex flex-col items-center justify-center gap-0.5">
                          <div className="flex items-center justify-center gap-1">
                            <input
                              key={`input-${rowId}-${foiEditado ? "editado" : "original"}-${valorFinal}`}
                              type="number"
                              step="0.001"
                              defaultValue={valorFinal}
                              onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                  e.target.blur();
                                }
                              }}
                              onBlur={(e) => {
                                const num = Math.round(parseNumeroBR(e.target.value) * 1000) / 1000;
                                if (Math.abs(num - valorFinal) > 0.0001) {
                                  if (Math.abs(num - valorOriginal) <= 0.0001) {
                                    onSaveEdition(rowId, null);
                                  } else {
                                    onSaveEdition(rowId, num);
                                  }
                                }
                              }}
                              className={`w-28 h-6 text-sm text-center font-bold rounded border px-1 ${foiEditado ? "border-cell-edited-border text-cell-edited-text bg-white" : "border-border"}`}
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
                          {tem30 && Math.abs(val30 - valorFinal) > 0.0001 && (
                            <div className="flex items-center justify-center gap-1 text-[10px] text-text-secondary">
                              <span>
                                30d:{" "}
                                <strong className="text-blue-700 font-mono">
                                  {val30.toLocaleString("pt-BR", { minimumFractionDigits: 3, maximumFractionDigits: 3 })}
                                </strong>
                              </span>
                              <button
                                type="button"
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  onSaveEdition(rowId, val30);
                                }}
                                className="text-blue-600 hover:text-blue-800 font-bold hover:underline flex items-center gap-0.5"
                                title={`Copiar sugestão de 30 dias (${val30})`}
                              >
                                <span className="material-symbols-outlined text-[11px]">
                                  bolt
                                </span>
                                Copiar
                              </button>
                            </div>
                          )}
                        </div>
                      </td>
                    );
                  }

                  let formatVal = linha[col] ?? "";
                  const isCurrency =
                    col === "Valor Comprado" || col === "Valor Estoque" || col === "Valor Unitário";

                  if (isCurrency && formatVal !== "") {
                    formatVal = parseNumeroBR(formatVal).toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                      minimumFractionDigits: 3,
                      maximumFractionDigits: 3,
                    });
                  } else if (
                    typeof formatVal === "number" ||
                    (typeof formatVal === "string" &&
                      formatVal.trim() !== "" &&
                      !isNaN(Number(formatVal.replace(",", "."))) &&
                      !col.includes("Data") &&
                      col !== "Item" &&
                      col !== "Status" &&
                      col !== "Baixa" &&
                      col !== "Família" &&
                      col !== "Analisar" &&
                      col !== "Ponto de pedido" &&
                      col !== "Faixa de compra" &&
                      col !== "texto OC" &&
                      col !== "Descrição" &&
                      col !== "Observação")
                  ) {
                    const num = typeof formatVal === "number" ? formatVal : parseNumeroBR(formatVal);
                    if (!Number.isNaN(num)) {
                      formatVal = num.toLocaleString("pt-BR", {
                        minimumFractionDigits: 3,
                        maximumFractionDigits: 3,
                      });
                    }
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

                  const isCenter = ehColunaCentralizada(col);
                  return (
                    <td
                      key={col}
                      className={`py-0.5 px-3 truncate max-w-[200px] ${
                        isCenter
                          ? "text-center"
                          : col === "Valor Comprado"
                            ? "font-bold text-right text-primary"
                            : "text-left"
                      } ${
                        foiEditado && col === "Valor Comprado"
                          ? "!text-cell-edited-text"
                          : ""
                      }`}
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
