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

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/Componente_Dashboard]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[01-Frontend-UI/Frontend_API_Client]] (chamadas `salvar_edicao`, `obter_slice`)
* **Bibliotecas Externas:** `react`.
