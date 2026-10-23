---
script: "backend/scripts/carrega_dados.py"
tipo: "automacao"
linguagem: "python"
gatilho: "manual"
data_atualizacao: 2026-10-14
tags: [automacao, script, python, etl, batch]
---

# Automação: backend/scripts/carrega_dados.py

**Objetivo:** Script batch modularizado para atualizar os arquivos de snapshot `.pkl` em `backend/data/snapshots/` a partir do ERP PCP, processar a base histórica de consumo de 4 meses anteriores (`backend/data/apont-YYYY-MM.csv`) e gerar os arquivos consolidados `backend/data/CSV/apoio.csv` e `backend/data/CSV/conf.csv` com filtro dos 5 registros mais recentes de fornecedores por item.

## Como é Executado (Gatilho)

- Executado manualmente via terminal:
  ```powershell
  python backend/scripts/carrega_dados.py
  ```
- Também pode ser disparado programaticamente via API através do método RPC `executar_carrega_dados`.

## Fluxo de Execução

1. Adiciona o diretório `backend/` ao `sys.path` para resolução segura de módulos.
2. Itera sobre a lista de análises configuradas em `app.settings.ANALISES`.
3. Executa a coleta via `app.services.pipeline.coletar_dados()` e salva os snapshots em `backend/data/snapshots/snapshot_{analise}.pkl`.
4. Carrega o snapshot gerado, lê o arquivo histórico de apontamentos (`backend/data/apont-YYYY-MM.csv`), agrupa quantidades por item e insere como coluna no DataFrame de apoio de compras.
5. Salva a base tratada em `backend/data/CSV/apoio.csv`.
6. Filtra o histórico de pontualidade de entregas (`conf.csv`), selecionando apenas empresa 11, removendo registros sem data válida e retendo as últimas 5 entregas de cada item em `backend/data/CSV/conf.csv`.

## Arquivos Afetados

**➡️ Modifica/Lê:**
* `backend/data/snapshots/snapshot_compra por necessidade.pkl`
* `backend/data/snapshots/snapshot_Geral.pkl`
* `backend/data/CSV/apoio.csv`
* `backend/data/CSV/conf.csv`
* `backend/data/apont-*.csv`
* [[04-Infra-Dados/Pipeline_Coleta]]
* [[04-Infra-Dados/Processador_Dados]]
* [[04-Infra-Dados/Configuracoes_Settings]]
