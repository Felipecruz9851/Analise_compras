---
modulo: "API_Router"
tipo: "backend"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, backend, python, api, rotas, rest]
---

# Módulo: API_Router (backend/app/api.py)

**Responsabilidade:** Concentrador das rotas e regras de negócio expostas para o cliente frontend. Implementa um padrão RPC via endpoint unificado `/api/call/{method}`, gerenciando chamadas de análise, paginação com filtros compostos, persistência de edições de compras, geração de relatórios OCs em HTML/CSV e gerenciamento de arquivos persistidos em `backend/data/`.

## Principais Funções / Métodos
* `call_method(method, req, response)`: Roteador de métodos RPC com injeção automática de estado da sessão.
* `rodar_analise(session, payload)`: Inicia execução protegida por `threading.Lock` para extração e processamento de compras.
* `obter_slice(session, payload)`: Processamento em memória de filtros (exato, parcial, invertido), ordenação e paginação do dataframe.
* `salvar_edicao(session, payload)`: Registra alterações manuais do usuário na quantidade de compras (`Decis Compras`).
* `gerar_ocs(session, payload)`: Gera arquivos de lote contendo HTML interativo e CSV para upload no ERP salvos em `settings.EXPORTS_DIR`.
* `executar_carrega_dados(session, payload)`: Transforma dados brutos dos snapshots `.pkl` em tabelas consolidadas em `settings.CSV_DIR`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Main_Server]]
* [[01-Frontend-UI/Frontend_API_Client]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[02-Backend-API/Session_Manager]]
* [[04-Infra-Dados/Pipeline_Coleta]]
* [[04-Infra-Dados/Processador_Dados]]
* [[04-Infra-Dados/Configuracoes_Settings]]
* **Bibliotecas Externas:** `fastapi`, `pandas`, `pydantic`.
