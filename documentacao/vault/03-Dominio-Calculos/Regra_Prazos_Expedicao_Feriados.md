---
modulo: "Regra_Prazos_Expedicao_Feriados"
tipo: "dominio"
data_atualizacao: 2026-10-14
tags: [regras-negocio, logistica, prazos, feriados, dias-uteis]
---

# Regra: Regra_Prazos_Expedicao_Feriados (backend/app/settings.py)

**Contexto:** Lógica logística para cálculo regressivo da data ideal de necessidade da matéria-prima. Para que o produto final chegue na data prometida ao cliente (`Entrega Pedido`), a matéria-prima deve estar disponível no almoxarifado antes do tempo de transporte/expedição até a região do cliente, considerando apenas dias úteis e o calendário corporativo de feriados.

## Lógica e Parâmetros

- **Variáveis de Entrada Obrigatórias:**
  - `rep`: Código identificador do Representante Comercial ou Região de Vendas (Integer).
  - `feriados.txt`: Lista oficial de datas não-úteis da empresa (Datas ISO YYYY-MM-DD em `backend/app/feriados.txt`).

- **Condicionais Críticas:**
  - **Mapeamento de Prazos por Representante:**
    - Representantes pontuais (`[7, 9, 95, 201, 202, 203, 241, 261, 700, 724, 762]`): Prazo de 3 dias úteis.
    - Representantes `601, 602, 603`: Prazo de 10 dias úteis.
    - Intervalo 50 a 90 ou 1000 a 1999: Prazo de 3 dias úteis.
    - Intervalo 2000 a 7999 ou 9000 a 9999: Prazo de 8 dias úteis.
    - Intervalos 300 a 499 ou 8000 a 8999: Prazo de 10 dias úteis.
    - Padrão (Fallback): 10 dias úteis.
  - **Retroação de Dias Úteis:** A `Data Ideal` é obtida recuando o prazo de expedição a partir da `Entrega Pedido` usando `np.busday_offset(..., offsets=-prazo, roll='backward', holidays=feriados_np)`.

- **Saída Esperada:**
  - Inteiro representando os dias de antecedência logística e cálculo da data ideal no calendário fabril.

## Dependências

**⬅️ Consumido por:** [[03-Dominio-Calculos/Regra_Compra_Necessidade]]
