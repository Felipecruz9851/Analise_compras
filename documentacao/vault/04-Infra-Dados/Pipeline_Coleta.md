---
modulo: "Pipeline_Coleta"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, infra, python, pipeline, orquestrador]
---

# Módulo: Pipeline_Coleta (backend/app/services/pipeline.py)

**Responsabilidade:** Orquestrador ponta-a-ponta do fluxo de dados localizado em `backend/app/services/pipeline.py`. Decide entre carregar snapshots salvos em disco (`backend/data/snapshots/*.pkl`) ou disparar nova extração web em lote, aciona o tratamento/concatenação dos DataFrames e alimenta as regras de cálculo de compras.

## Principais Funções / Métodos
* `coletar_dados(username, password, analise)`: Extrai dados ao vivo via `Extractor` ou restaura o arquivo pickle local a partir de `settings.SNAPSHOTS_DIR` caso `username` seja vazio.
* `executar_pipeline(username, password, analise)`: Executa a coleta, invoca o cálculo de compra por necessidade, injeta identificadores únicos universais (`__rowId` UUID4) e exporta em formato de lista de registros (Records).

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/API_Router]]
* [[05-Automacoes/Script_Carrega_Dados]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[04-Infra-Dados/Extrator_PCP]]
* [[04-Infra-Dados/Processador_Dados]]
* [[03-Dominio-Calculos/Regra_Compra_Necessidade]]
* [[04-Infra-Dados/Configuracoes_Settings]]
* **Bibliotecas Externas:** `pandas`, `pickle`, `uuid`.
