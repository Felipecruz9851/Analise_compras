---
modulo: "Session_Manager"
tipo: "backend"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, backend, python, session, thread-safety, contextvars]
---

# Módulo: Session_Manager (backend/app/session_manager.py, backend/app/context.py)

**Responsabilidade:** Gerenciamento do ciclo de vida das sessões de usuário em memória (`SessionState`). Provê isolamento multiusuário com thread-safety (`threading.Lock`), expiração automática por Time-to-Live (TTL de 2 horas) e propagação contextual assíncrona com `ContextVar`.

## Principais Funções / Métodos
* `SessionState`: Classe de estado que encapsula dataframes carregados (`df_base`, `df_ativo`), dicionário de edições manuais e travas de concorrência.
* `get_session(session_id)`: Retorna a sessão ativa associada ao ID fornecido e realiza a purga de sessões inativas/expiradas.
* `session_id_var`: Instância global de `contextvars.ContextVar` usada para identificar a requisição corrente sem acoplamento direto de parâmetros.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Main_Server]] (via middleware)
* [[02-Backend-API/API_Router]]

**➡️ Quem este módulo chama (Saída/Uso):**
* **Bibliotecas Externas:** `threading`, `time`, `contextvars` (Padrão Python).
