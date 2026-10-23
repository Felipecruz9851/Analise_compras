---
modulo: "Legacy_WebView_UI"
tipo: "frontend"
linguagem: "javascript"
data_atualizacao: 2026-10-14
tags: [codigo, frontend, legacy, html, webview]
---

# Módulo: Legacy_WebView_UI (backend/app/ui/*, backend/app/ui/webview_app.py)

**Responsabilidade:** Conjunto de interfaces legadas implementadas originalmente para execução desktop local via biblioteca Python `pywebview`. Composto por páginas HTML estáticas (`login.html`, `pagina_resultado.html`), estilos CSS e ponte JS nativa, localizadas em `backend/app/ui/`.

## Principais Funções / Métodos
* `webview_app.py: Api.call()`: Despachante interno de métodos Python para o contexto JavaScript do pywebview.
* `api_polyfill.js`: Emulador de chamadas para permitir funcionamento híbrido no navegador sem a runtime do webview.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Main_Server]] (montado como fallback estático em `/ui/`)

**➡️ Quem este módulo chama (Saída/Uso):**
* [[04-Infra-Dados/Pipeline_Coleta]]
* **Bibliotecas Externas:** `pywebview`.
