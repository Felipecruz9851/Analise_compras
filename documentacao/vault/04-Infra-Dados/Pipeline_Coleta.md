---
modulo: "Pipeline_Coleta"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-23
tags: [codigo, infra, python, pipeline, orquestrador, extracao-unificada]
---

# Módulo: Pipeline_Coleta (`backend/app/services/pipeline.py`)

**Responsabilidade:** Orquestrador ponta-a-ponta do fluxo de dados localizado em `backend/app/services/pipeline.py`. Decide entre carregar o snapshot master salvo em disco (`backend/data/snapshots/snapshot_Geral.pkl`) ou disparar nova extração unificada via `Extractor`, aciona a junção das tabelas e alimenta as regras de cálculo e projeção com filtragem por família.

## Principais Funções / Métodos
* `coletar_dados(username="", password="", analise="Geral")`: Extrai dados ao vivo via `Extractor` unificado ou restaura o arquivo pickle local prioritariamente de `snapshot_Geral.pkl` (com fallback para `snapshot_{analise}.pkl`) a partir de `settings.SNAPSHOTS_DIR` caso `username` seja vazio.
* `executar_pipeline(username, password, analise)`: Executa a coleta, delega para `calcular_com_apoio_30(analise, dfs)` (que filtra as famílias correspondentes e calcula o grupo selecionado), injeta identificadores únicos universais (`__rowId` UUID4) e exporta em formato de lista de dicionários (Records).

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/API_Router]]
* [[05-Automacoes/Script_Carrega_Dados]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[04-Infra-Dados/Extrator_PCP]]
* [[04-Infra-Dados/Processador_Dados]]
* [[03-Dominio-Calculos/Regra_Compra_Necessidade]]
* [[03-Dominio-Calculos/Motor_Analise_Estoque_Geral]]
* [[04-Infra-Dados/Configuracoes_Settings]]
* **Bibliotecas Externas:** `pandas`, `pickle`, `uuid`.
