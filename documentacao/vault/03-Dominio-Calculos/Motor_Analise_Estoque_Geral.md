---
modulo: "Motor_Analise_Estoque_Geral"
tipo: "dominio"
data_atualizacao: 2026-10-23
tags: [regras-negocio, calculo, analise-estoque, geral, excel, purchase-logic]
---

# Motor de Cálculo: Análise de Estoque Geral (`analise_estoque.py` & `purchase_logic.py`)

**Contexto:** Motor avançado de inteligência de compras e reposição de estoque que reproduz e estende as regras da planilha corporativa (`ANALISE DE COMPRAS.xlsx`). Integrado ao pipeline via `backend/app/services/analise_estoque.py` e executado pela função `geral(dfs)` em `backend/app/services/purchase_logic.py`, com projeção completa de métricas de diagnóstico na UI React (`PurchaseTable.jsx`).

## Lógica e Parâmetros

### 1. Entradas e Pré-processamento
- **`df_apoio` (`apoio_compras`):**
  - Identificação: `Item`, `Descrição` (mapeado de `Desc`), `Observação` (mapeado de `Obs.`), `Família` (`Familia`).
  - Meses dinâmicos: 5 colunas no padrão `AAAA-MM` (detectadas por `detectar_meses`): os 4 meses anteriores formam o histórico (`Cons 1` a `Cons 4`) e o mais recente é o `Cons mês atual`.
  - Estoques e Lotes: `Estoque Padrão`, `Estoque Produção` (`Estoque prod.`), `OC` (`OC.`), `Neces` (`Neces.`), `Baixa`, `Lote Mínimo` (`Lote min.`), `Lote Econom` (`Lote mult.`), `Prazo Fornecedor` (`Prazo cadastrado`), `Valor Unitário` (`Valor unitário`).
- **`df_entrega` (`conf`):**
  - Histórico de recebimentos filtrado por empresa `11`, ordenado cronologicamente decrescente e limitado às 5 entregas mais recentes por item.
  - Determinação da `Média prazos de entrega (5 - 3 últimos)`: se o item possuir menos de 3 entregas, adota o prazo cadastrado.

### 2. Parâmetros de Configuração (`config_parametros.json`)
- **Faixas de Compra:**
  - Faixa A: cobertura 7 dias, recebimentos máx 3, ciclo 0.
  - Faixa B: cobertura 20 dias (ou 15 conforme calibração), recebimentos máx 3, ciclo 0.
  - Faixa C: cobertura 60 dias, recebimentos máx 3, ciclo 0.
- **Teto de Compra:** R$ 2.000,00.
- **Estoque de Segurança:** 5 dias (ou 7 dias).

### 3. Fórmulas de Domínio
- **Consumo Diário (`Cons diário` / `Média Diária`):**
  - Base: média de `Cons 1` a `Cons 4` dividida por 30.
  - Fallback: se média for 0, calcula `(Neces + Cons mês atual) / 60`.
- **Saldo Virtual (`Saldo Virtual`):**
  - `Colunas1 = OC + Estoque Produção + Estoque Padrão - Neces`.
  - Regra Especial `REV`: se zeros em histórico <= 3, `Neces >= 0`, família `REV` e `Colunas1 <= 30`, desconta 50 unidades (`Colunas1 - 50`).
  - Regra `Baixa`: se `Baixa == 'N'`, fixa em `Estoque Padrão + OC`.
- **Média mensal + Necessidade:**
  - Se `Baixa == 'S'`: média dos valores não-nulos considerando histórico e necessidade (`Cons 1..4` e `Neces`).
  - Se `Baixa != 'S'`: média dos valores não-nulos apenas do histórico (`Cons 1..4`).
- **Auditoria Operacional:**
  - **`Analisar`:** sinaliza `"ANALIZAR"` se `Saldo virtual <= Média mens + Necessidade`, se inicia com `#`, `$`, `~*`, ou se desvio relativo > 70%.
  - **`Status`:** classificação em `X` (consumo constante), `Y` (intermitente), `Z` (sem consumo com saldo) ou `Y@`.
- **Índices e Fator de Ajuste:**
  - `Fator de ajuste = Ajuste cons + Ajuste futuro + Ajuste de entrega`.
  - `Cobertura mínima (dias) = round_excel(estoque_seguranca * (1 + Fator) + Prazo Fornecedor)`.
- **Ponto de Pedido e Sugestão:**
  - `Ponto de pedido`: `"comprar"` se `Dias de saldo virtual <= Cobertura mínima + 7` (e status não-Z); senão `"ok"`.
  - `Sugestão de compra (dias)` e `Compra com ajuste (dias)`: dimensiona dias necessários para recompor cobertura e ciclo de lote.
  - `QTD COMPRA = Compra com ajuste (dias) * Consumo diário`.
  - `Decis Compras`: quantificação final arredondada para `Lote Mínimo` e múltiplos de `Lote Econom`.
  - `Valor Comprado = Decis Compras * Valor Unitário`.

### 4. Enriquecimento de Dados, Vetorização SIMD e Compatibilidade Frontend
- **Vetorização de Alta Performance (Eliminação de `iterrows`):**
  - O motor em `backend/app/services/analise_estoque.py:processar_analise_compras` opera de forma 100% vetorizada com NumPy e Pandas nativo.
  - Foram eliminados os 10 laços `for idx, r in res.iterrows():` que instanciadavam mais de 760 mil objetos `pd.Series`, reduzindo o tempo do motor sobre 76.641 registros de **~17.2s para 0.30s (aceleração de ~57x)** com **100.0% de paridade double-entry** em todas as 43 colunas.
- **Colunas Complementares e Resiliência a Duplicatas ERP:**
  - `Valor Estoque = Estoque Padrão * Valor Unitário`.
  - `Data OC`: data útil calculada somando `Prazo Fornecedor` à data corrente, ajustada pelo calendário de dias úteis e feriados corporativos (`np.busday_offset`).
  - `Falta`: `max(0, Neces - (Estoque Produção + Estoque Padrão + OC))`.
  - `texto OC`: inicializado vazio para exportação de ordens no ERP.
  - Metadados: `Última Data Entrada`, `Última Data Saída`, `Estoque Rejeitado`, `Família`.
  - **Tratamento de Chaves Duplicadas (`InvalidIndexError`):** Itens com duplicidade cadastral no ERP são vinculados mantendo o alinhamento posicional 1:1 com `df_apoio`, com fallback via `drop_duplicates(subset=['Item'])` para garantir que o pandas nunca execute `reindex` ou `map` sobre índices não-únicos.
- **Exposição na Tabela (`PurchaseTable.jsx`):**
  - Todas as 35+ colunas são mantidas após o filtro de `colunas_desejadas`.
  - As 5 colunas de mês (`AAAA-MM`) são agrupadas dinamicamente na coluna de sparkline `Gráfico`.
  - `Decis Compras` (editável) e `Valor Comprado` (moeda BRL) recebem destaque visual na interface.

## Dependências

- **⬅️ Consome:** `backend/app/services/analise_estoque.py`, `backend/app/settings.py` (feriados), `backend/data/CSV/conf.csv`, `backend/data/CSV/apoio.csv`.
- **➡️ Consumido por:** [[00-Visao-Geral/Index_Analise_compras]], [[01-Frontend-UI/Componente_PurchaseTable]], [[02-Backend-API/Main_Server]], `backend/app/ui/webview_app.py`.
