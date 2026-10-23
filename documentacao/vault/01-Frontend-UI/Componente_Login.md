---
modulo: "Componente_Login"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, react, autenticacao]
---

# Módulo: Componente_Login (frontend/src/components/Login.jsx)

**Responsabilidade:** Interface de autenticação do usuário, permitindo informar credenciais do PCP, selecionar a análise de compras desejada, disparar a extração em lote e gerenciar os snapshots salvos no backend.

## Principais Funções / Métodos
* `handleLogin(e)`: Dispara a execução do pipeline de compras através da rota `rodar_analise`.
* `carregarAnalises()`: Obtém a listagem dinâmica de tipos de análise disponíveis no backend (`/api/listar_analises`).
* `handleGerarDados()`: Dispara a rotina em segundo plano para gerar e atualizar arquivos pickle (`backend/data/snapshots/`).
* `handleCarregarPickles()`: Lista os arquivos de snapshot existentes no servidor.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/React_App]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[01-Frontend-UI/Frontend_API_Client]]
* [[02-Backend-API/API_Router]] (chamadas `rodar_analise`, `gerar_pickles`, `listar_pickles`)
* **Bibliotecas Externas:** `react`.
