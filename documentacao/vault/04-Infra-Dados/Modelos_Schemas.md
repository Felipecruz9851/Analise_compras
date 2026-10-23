---
modulo: "Modelos_Schemas"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, infra, python, schemas, dataclasses, pydantic]
---

# Módulo: Modelos_Schemas (backend/app/models/schemas.py)

**Responsabilidade:** Definição dos contratos de dados (DTOs) e estruturas tipadas para entradas da API e parâmetros de execução de análise localizados em `backend/app/models/schemas.py`.

## Principais Funções / Métodos
* `AnaliseInput`: Dataclass contendo `username`, `password` e `analise`.
* `CallPayload`: Modelo Pydantic para validação das requisições RPC no roteador `/api/call/{method}`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/API_Router]]

**➡️ Quem este módulo chama (Saída/Uso):**
* **Bibliotecas Externas:** `pydantic`, `dataclasses`.
