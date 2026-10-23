---
modulo: "Componente_MetricsCards"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, react, graficos, kpi]
---

# Módulo: Componente_MetricsCards (frontend/src/components/MetricsCards.jsx)

**Responsabilidade:** Apresentação dos indicadores-chave de desempenho (KPIs) da análise de compras atual, exibindo o valor total planejado, total de OCs prontas e distribuição orçamentária por famílias de materiais.

## Principais Funções / Métodos
* `MetricsCards({ resumo, totalGeral, totalOcsProntas })`: Renderiza os cards de métricas sintetizadas e badges percentuais de representatividade financeira.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/Componente_Dashboard]]

**➡️ Quem este módulo chama (Saída/Uso):**
* **Bibliotecas Externas:** `react`, `chart.js` (opcional), `react-chartjs-2`.
