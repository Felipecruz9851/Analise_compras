---
modulo: "Main_Server"
tipo: "backend"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, backend, python, fastapi, uvicorn]
---

# Módulo: Main_Server (backend/main.py)

**Responsabilidade:** Servidor de aplicação principal FastAPI localizado em `backend/main.py`. Inicializa o pipeline de middlewares assíncronos (gestão de cookies de sessão), registra os roteadores da API, monta os diretórios de arquivos estáticos de dados (`backend/data/exports/`, `backend/data/CSV/`), entrega a SPA compilada do React (`frontend/dist/`) e inicia o servidor Uvicorn.

## Principais Funções / Métodos
* `SessionMiddleware.dispatch()`: Intercepta cada requisição HTTP, extrai ou gera cookie `session_id` e associa à variável de contexto assíncrona `session_id_var`.
* `serve_frontend(full_path)`: Catch-all route que entrega os arquivos estáticos compilados do React a partir de `frontend/dist` ou serve o `index.html` (SPA fallback).
* `app.mount(...)`: Montagem dos endpoints estáticos `/exports` (`settings.EXPORTS_DIR`), `/csv_files` (`settings.CSV_DIR`) e `/assets` (`dist/assets`).

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* Clientes Web / Navegadores HTTP
* [[01-Frontend-UI/Frontend_API_Client]]
* Uvicorn runner (`python backend/main.py`)

**➡️ Quem este módulo chama (Saída/Uso):**
* [[02-Backend-API/API_Router]]
* [[02-Backend-API/Session_Manager]]
* [[04-Infra-Dados/Configuracoes_Settings]]
* **Bibliotecas Externas:** `fastapi`, `uvicorn`, `starlette`.
