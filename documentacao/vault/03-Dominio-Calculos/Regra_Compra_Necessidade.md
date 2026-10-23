---
modulo: "Regra_Compra_Necessidade"
tipo: "dominio"
data_atualizacao: 2026-10-14
tags: [regras-negocio, calculo, parametros, mrp, compras]
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

## Dependências

**⬅️ Consumido por:** [[04-Infra-Dados/Pipeline_Coleta]], [[02-Backend-API/API_Router]]
