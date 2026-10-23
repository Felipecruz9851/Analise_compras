---
modulo: "React_App"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, react, vite]
---

# Módulo: React_App (frontend/src/App.jsx, frontend/src/main.jsx)

**Responsabilidade:** Ponto de entrada e orquestração de visualização da Single Page Application (SPA) em React 19 localizada em `frontend/`. Gerencia o chaveamento de tela entre a autenticação inicial e o painel operacional analítico.

## Principais Funções / Métodos
* `App()`: Componente raiz (`frontend/src/App.jsx`) que mantém o estado da visualização atual (`login` ou `dashboard`).
* `main.jsx`: Bootstrap do React (`frontend/src/main.jsx`) utilizando `createRoot` e injeção do CSS base do Tailwind.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[00-Visao-Geral/Index_Analise_compras]]
* `frontend/index.html` (Carregado pelo Vite Bundler)

**➡️ Quem este módulo chama (Saída/Uso):**
* [[01-Frontend-UI/Componente_Login]]
* [[01-Frontend-UI/Componente_Dashboard]]
* **Bibliotecas Externas:** `react`, `react-dom`.
