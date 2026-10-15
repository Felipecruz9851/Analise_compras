---
modulo: "Frontend_API_Client"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, javascript, http, api, fetch]
---

# Módulo: Frontend_API_Client (frontend/src/services/api.js)

**Responsabilidade:** Camada de cliente HTTP responsável pela comunicação assíncrona com o backend FastAPI. Implementa envio seguro de cookies de sessão (`credentials: 'include'`), tratamento centralizado de exceções e padronização das chamadas RPC para `/api/call/{method}`.

## Principais Funções / Métodos
* `apiCall(method, payload)`: Envia requisição POST parametrizada para o backend com serialização JSON e validação do payload de resposta.
* `listarAnalises()`: Executa chamada GET direta para `/api/listar_analises`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[01-Frontend-UI/Componente_Login]]
* [[01-Frontend-UI/Componente_Dashboard]]
* [[01-Frontend-UI/Componente_PurchaseTable]]
* [[01-Frontend-UI/Componente_ConfigEditor]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[02-Backend-API/Main_Server]] (`/api/...`)
* [[02-Backend-API/API_Router]]
* **Bibliotecas Externas:** `fetch` (Nativa do Navegador / ES6).
