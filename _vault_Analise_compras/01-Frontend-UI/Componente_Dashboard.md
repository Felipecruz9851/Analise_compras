---
modulo: "Componente_Dashboard"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, react, dashboard]
---

# Módulo: Componente_Dashboard (frontend/src/components/Dashboard.jsx)

**Responsabilidade:** Tela principal de trabalho do comprador. Integra barra de ações para geração de OCs, acionamento de editor de parâmetros, exportação em lote e orquestra a tabela de compras com os cartões de métricas.

## Principais Funções / Métodos
* `carregarDados(pagina, filtros, ordenacao)`: Busca fatias paginadas de dados processados no servidor via `obter_slice`.
* `handleGerarOcs()`: Dispara geração de relatórios estáticos em HTML e arquivos CSV salvos em `backend/data/exports/`.
* `handleExportarVisivel()`: Exporta apenas a visão filtrada pelo usuário em tela.
* `handleAbrirPasta()`: Abre o diretório local de exportações (`backend/data/exports/`) no sistema operacional do servidor.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/React_App]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[01-Frontend-UI/Componente_Header_Sidebar]]
* [[01-Frontend-UI/Componente_MetricsCards]]
* [[01-Frontend-UI/Componente_PurchaseTable]]
* [[01-Frontend-UI/Componente_ConfigEditor]]
* [[01-Frontend-UI/Frontend_API_Client]]
* **Bibliotecas Externas:** `react`.
