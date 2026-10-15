---
modulo: "Regra_Calculo_Estoque_Regras"
tipo: "dominio"
data_atualizacao: 2026-10-14
tags: [regras-negocio, calculo, parametros, engine, vetorizacao]
---

# Regra: Regra_Calculo_Estoque_Regras (backend/app/services/calc_est.py)

**Contexto:** Motor de execução de regras dinâmicas e fórmulas vetoriais para classificação de estoque (curvas XYZ, ponto de pedido, dias de cobertura e lote de reposição) executado em alta performance com NumPy e Pandas em `backend/app/services/calc_est.py`.

## Lógica e Parâmetros

- **Variáveis de Entrada Obrigatórias:**
  - `estoque`: Quantidade em estoque físico (Float).
  - `compras`: Quantidade já pedida ao fornecedor (Float).
  - `necessidade`: Necessidade acumulada de produção (Float).
  - `consumo_90`: Consumo histórico nos últimos 90 dias (Float).
  - `cobertura`: Dias de cobertura desejados pela política de estoque (Float).
  - `lote_min` e `lote_mult`: Parâmetros de fornecimento (Float).

- **Condicionais Críticas:**
  - `consumo_dia = div(consumo_90, 90)` (Divisão segura protegida contra divisão por zero).
  - `saldo_virtual = estoque + compras - necessidade`.
  - `dias_saldo = div(saldo_virtual, consumo_dia, 9999)`.
  - **Ponto de Pedido:** Se `dias_saldo < cobertura`, status é `COMPRAR`, senão `OK`.
  - **Classificação XYZ:**
    - `X`: Consumo regular em todos os três períodos (`cons_1 != 0 & cons_2 != 0 & cons_3 != 0`).
    - `Z`: Consumo nulo nos 3 períodos sem demanda ativa e com saldo virtual remanescente.
    - `Y`: Demanda intermitente ou flutuante.

- **Saída Esperada:**
  - Classificação operacional dos materiais, quantidade recomendada de reposição e indicação de ponto de pedido.

## Dependências

**⬅️ Consumido por:** [[00-Visao-Geral/Index_Analise_compras]]
