---
modulo: "Regra_Compra_Necessidade"
tipo: "dominio"
data_atualizacao: 2026-10-23
tags: [regras-negocio, calculo, parametros, mrp, compras, otimizacao]
---

# Regra: Regra_Compra_Necessidade (backend/app/services/purchase_logic.py)

**Contexto:** Lógica central de Planejamento de Necessidade de Materiais (MRP) para itens de compras. Calcula o saldo líquido disponível, compara com a demanda de ordens de produção em aberto, desconta estoque em quarentena/rejeitado e quantifica a ordem de compra respeitando lotes mínimos e múltiplos econômicos.

## Lógica e Parâmetros

- **Variáveis de Entrada Obrigatórias:**
  - `Neces`: Quantidade total demandada pelas ordens de produção (Float).
  - `Estoque Padrão`: Quantidade física em almoxarifado (Float).
  - `Estoque Produção`: Quantidade alocada em chão de fábrica (Float).
  - `Estoque Rejeitado`: Quantidade segregada com defeito no controle de qualidade (Float).
  - `OC`: Quantidade de ordens de compra já emitidas e com entrega pendente (Float).
  - `Lote Mínimo`: Quantidade mínima aceita pelo fornecedor para emissão de pedido (Float).
  - `Lote Econom`: Múltiplo de embalagem ou lote econômico de compra (Float).
  - `Prazo Fornecedor`: Lead time padrão do fornecedor em dias corridos (Integer).

- **Condicionais Críticas:**
  - **Cálculo da Falta:** `Falta = Neces - (Estoque Produção + Estoque Padrão + OC + Estoque Rejeitado)`.
  - Se `Falta <= 0`: `Decis Compras = 0` (Não comprar).
  - Se `0 < Falta <= Lote Mínimo`: `Decis Compras = Lote Mínimo`.
  - Se `Falta > Lote Mínimo`: `Decis Compras = Lote Mínimo + ceil((Falta - Lote Mínimo) / Lote Econom) * Lote Econom`.
  - **Filtro especial Família 'VRG' (Vidraçaria/Mármores):** Se o item for da família VRG e não satisfazer critérios de prazo (limite 28 dias), representante comercial específico (50 a 100) ou fábrica restrita, a compra é forçada a 0 para postergação de capital.

- **Saída Esperada:**
  - DataFrame enriquecido com colunas: `Decis Compras`, `Valor Comprado`, `Data OC`, `Data Ideal`, `texto OC` formatado para integração ERP e histórico de consumo mensal (lido de `backend/data/apont-*.csv`).
  - Suporte à coluna comparativa de 30 dias (`_N30`) gerada transparentemente via `calcular_com_apoio_30(analise, dfs)`.

## Otimizações de Alta Performance (2026-10-23)

O motor foi reformulado para processar o rateio de 33.055 registros de apoio contra 171.000 consumos de forma ultra-eficiente sem alterar 1 único bit dos resultados:
1. **Dicionário de Consumo Global em $O(N)$:** Em vez de executar 15.387 `groupby` e `sort_values` individuais com `df.groupby()`, ordena-se `df_consumo` globalmente uma única vez e agrupa-se em dicionário nativo Python via iteração rápida (tempo reduzido de 30,5s para 3,9s).
2. **Iteração Otimizada no Rateio:** O rateio iterativo agora utiliza `df.to_dict("records")` e clonagem nativa `dict(row_base)`, eliminando a criação de 33.000 instâncias de `pd.Series` por `iterrows()`.
3. **Pós-processamento Vetorizado com NumPy:**
   - Preenchimento de atributos de raiz (`raiz_Item Final`, etc.) vetorizado via `.map()` e `.loc[]` (de 8,5s para 0,05s).
   - Cálculo de `Data Ideal` e regras da família `VRG` vetorizados via `np.busday_offset` e máscaras booleanas (de 8,0s para 0,10s).
4. **Ganhos de Performance Validados:**
   - Cálculo central reduzido de **38,59s** para **12,65s** (aceleração de **3,1x a 9x mais rápido**).
   - Teste de regressão double-entry confirmou **100.0% de paridade** em todas as 33 colunas e 33.055 registros (`max diff = 0.000000`).
   - Carregamento ponta a ponta validado via Chrome Headless em `http://366n:8686/` com 33.055 itens e 63 OCs prontas.

## Dependências

**⬅️ Consumido por:** [[04-Infra-Dados/Pipeline_Coleta]], [[02-Backend-API/API_Router]]
**➡️ Conecta com:** [[Motor_Analise_Estoque_Geral]], [[Index_Analise_compras]]
