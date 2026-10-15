---
modulo: "Regra_Rateio_Consumo_Grafo"
tipo: "dominio"
data_atualizacao: 2026-10-14
tags: [regras-negocio, calculo, grafo, bfs, estrutura-produto, rateio]
---

# Regra: Regra_Rateio_Consumo_Grafo (backend/app/services/processor.py: calc_data)

**Contexto:** Resolução em árvore de dependência de manufatura (BOM - Bill of Materials). Uma matéria-prima adquirida (ex: chapa, parafuso, tecido) é consumida em ordens intermediárias de subconjuntos, que por sua vez compõem outras ordens até o produto acabado final (ex: sofá, armário, mesa). Este algoritmo reconstrói o grafo pai-filho e propaga os dados do pedido raiz até a compra.

## Lógica e Parâmetros

- **Variáveis de Entrada Obrigatórias:**
  - `ordens`: Tabela com ordens de produção em aberto (`Ordem Prod`, `Item`, `Saldo`, `Pedido`, `Entrega Pedido`, `Cliente`, `Representante`).
  - `cons`: Tabela de consumo de componentes (`Item`, `Ordem Cons`, `Consumo`, `Local Prod.`, `Tipo`).
  - `estoque`: Tabela de saldo em estoque dos itens.

- **Condicionais Críticas:**
  - **Identificação da Raiz:** Itens pai que não existem na lista de componentes são identificados como Nós Raízes (Produtos Finais vendidos ao cliente).
  - **Busca em Largura (BFS Top-Down):** O algoritmo itera em até 12 níveis na árvore hierárquica. Em cada nível, busca a correspondência entre a ordem de consumo do filho e o cache raiz dos pais, usando `(Ordem Cons, Pedido_Ordem, Pedido_Contexto)` para desambiguação de múltiplos pedidos simultâneos.
  - **Rateio Mutável Sem Duplicação:** Quando uma quantidade de compra é calculada, ela consome as demandas no grafo abatendo o saldo disponível em ordem decrescente de OP, prevenindo dupla alocação financeira.

- **Saída Esperada:**
  - DataFrame de consumo mapeado com atributos da raiz: `raiz_Item Final`, `raiz_Pedido`, `raiz_Entrega Pedido`, `raiz_Representante`, `raiz_Cliente`, `raiz_Fábrica`.

## Dependências

**⬅️ Consumido por:** [[03-Dominio-Calculos/Regra_Compra_Necessidade]], [[02-Backend-API/API_Router]]
