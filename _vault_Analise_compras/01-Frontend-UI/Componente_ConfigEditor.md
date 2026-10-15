---
modulo: "Componente_ConfigEditor"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, react, configuracao]
---

# Módulo: Componente_ConfigEditor (frontend/src/components/ConfigEditor.jsx)

**Responsabilidade:** Modal/Painel interativo para visualização e edição das regras e parâmetros de cálculo de compras (estoque de segurança, limites, multiplicadores de lote) salvos em `backend/app/services/config_parametros.json`.

## Principais Funções / Métodos
* `carregarParametros()`: Efetua requisição ao backend para obter a árvore de configurações JSON ativa via `obter_parametros`.
* `salvarParametros()`: Submete as alterações validadas pelo usuário para gravação permanente no servidor via `salvar_parametros`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/Componente_Dashboard]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[01-Frontend-UI/Frontend_API_Client]] (métodos `obter_parametros`, `salvar_parametros`)
* **Bibliotecas Externas:** `react`.
