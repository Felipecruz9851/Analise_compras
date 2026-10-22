---
modulo: "Componente_PurchaseTable"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, react, tabela, edicao]
---

# Módulo: Componente_PurchaseTable (frontend/src/components/PurchaseTable.jsx)

**Responsabilidade:** Renderização da tabela de dados de análise de compras com edição em tempo real da coluna 'Decis Compras', filtros por cabeçalho (exato/parcial/invertido), ordenação dinâmica e formatação condicional de células.

## Principais Funções / Métodos
* `handleCellEdit(rowId, valor)`: Persiste imediatamente no servidor a quantidade comprada ajustada pelo usuário via `salvar_edicao`.
* `handleSort(coluna)`: Aplica ordenação ascendente/descendente na coluna selecionada.
* `handleFilterChange(coluna, valor)`: Atualiza critérios de filtragem e reinicia a paginação para a primeira página.
* `ehColunaMes(col)` & Sparkline: Detecta colunas com formato `AAAA-MM`, remove-as da listagem de texto plano e renderiza o minigráfico Sparkline agrupado na coluna `Gráfico` (posição 2).
* Projeção Dinâmica: Renderiza automaticamente todas as colunas fornecidas pelo backend (35+ colunas da análise geral e de necessidade), aplicando largura expandida para `Descrição` e formatação monetária para `Valor Comprado`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/Componente_Dashboard]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[01-Frontend-UI/Frontend_API_Client]] (chamadas `salvar_edicao`, `obter_slice`)
* **Bibliotecas Externas:** `react`.
