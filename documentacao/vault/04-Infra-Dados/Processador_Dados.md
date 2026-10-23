---
modulo: "Processador_Dados"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, infra, python, pandas, sanitizacao, etl]
---

# Módulo: Processador_Dados (backend/app/services/processor.py)

**Responsabilidade:** Camada de Engenharia de Dados (ETL) localizada em `backend/app/services/processor.py`. Realiza limpeza e normalização estatística de colunas, conversão de formatos de data/número brasileiros para padrões computacionais, consolidação de tabelas particionadas e resolução de estruturas de produtos.

## Principais Funções / Métodos
* `sanitizar_dataframe(df, limite=0.8)`: Inferência e conversão automática de tipos de dados (datas em `DD/MM/YYYY`, números flutuantes com vírgula e strings limpas).
* `juntar_tabelas(resultados)`: Agrupa e concatena com segurança DataFrames particionados por família ou local de produção.
* `calc_data(dfs)`: Montagem da estrutura relacional de ordens de produção e cálculo do grafo de consumo.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[04-Infra-Dados/Pipeline_Coleta]]
* [[03-Dominio-Calculos/Regra_Compra_Necessidade]]
* [[02-Backend-API/API_Router]]
* [[05-Automacoes/Script_Carrega_Dados]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[03-Dominio-Calculos/Regra_Rateio_Consumo_Grafo]]
* **Bibliotecas Externas:** `pandas`, `tqdm`.
