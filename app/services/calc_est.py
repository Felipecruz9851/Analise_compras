import time
import pandas as pd
import numpy as np

# =========================================================
# FUNÇÕES REGISTRADAS
# =========================================================
#
# Todas funções disponíveis dentro das fórmulas
#
# =========================================================


def div(a, b, default=0):
    """
    Divisão segura
    """

    return np.where(b == 0, default, a / b)


FUNCOES = {
    "np": np,
    "ceil": np.ceil,
    "floor": np.floor,
    "abs": np.abs,
    "round": np.round,
    "div": div,
}


# =========================================================
# BASE DE DADOS
# =========================================================

df = pd.DataFrame(
    {
        "item": ["A", "B", "C", "D", "E", "F", "G", "H"],
        "familia": ["ACO", "ACO", "LAM", "ELE", "ACO", "IMP", "LAM", "ACO"],
        "estoque": [100, 20, 5, 300, 0, 12, 50, 8],
        "compras": [0, 10, 0, 0, 100, 0, 0, 2],
        "necessidade": [30, 50, 15, 40, 120, 0, 10, 50],
        "cons_1": [30, 0, 0, 120, 80, 0, 15, 5],
        "cons_2": [30, 0, 0, 120, 100, 0, 20, 0],
        "cons_3": [30, 0, 0, 120, 90, 0, 30, 0],
        "consumo_90": [90, 0, 0, 360, 270, 0, 65, 5],
        "cobertura": [45, 30, 20, 60, 40, 10, 25, 15],
        "lote_min": [50, 100, 25, 200, 500, 20, 50, 10],
        "lote_mult": [10, 25, 5, 50, 100, 10, 25, 5],
    }
)


print("\n================ BASE ================\n")
print(df)


# =========================================================
# REGRAS
# =========================================================

REGRAS = [
    # =====================================================
    # CONSUMO MÉDIO
    # =====================================================
    {
        "ordem": 1,
        "tipo": "eval",
        "coluna": "consumo_dia",
        "formula": "div(consumo_90, 90)",
        "descricao": "Consumo médio diário",
    },
    # =====================================================
    # SALDO VIRTUAL
    # =====================================================
    {
        "ordem": 2,
        "tipo": "eval",
        "coluna": "saldo_virtual",
        "formula": "estoque + compras - necessidade",
        "descricao": "Saldo futuro",
    },
    # =====================================================
    # DIAS DE SALDO
    # =====================================================
    {
        "ordem": 3,
        "tipo": "eval",
        "coluna": "dias_saldo",
        "formula": "div(saldo_virtual, consumo_dia, 9999)",
        "descricao": "Quantidade de dias restantes",
    },
    # =====================================================
    # STATUS OPERACIONAL
    # =====================================================
    {
        "ordem": 4,
        "tipo": "select",
        "coluna": "status",
        "descricao": "Classificação operacional",
        "regras": [
            {
                "quando": "(cons_1 != 0) & " "(cons_2 != 0) & " "(cons_3 != 0)",
                "resultado": "'X'",
            },
            {
                "quando": "(cons_1 == 0) & "
                "(cons_2 == 0) & "
                "(cons_3 == 0) & "
                "(necessidade <= 0) & "
                "(saldo_virtual > 0)",
                "resultado": "'Z'",
            },
        ],
        "default": "'Y'",
    },
    # =====================================================
    # PONTO DE PEDIDO
    # =====================================================
    {
        "ordem": 5,
        "tipo": "where",
        "coluna": "ponto_pedido",
        "condicao": "dias_saldo < cobertura",
        "verdadeiro": "'COMPRAR'",
        "falso": "'OK'",
        "descricao": "Necessidade de compra",
    },
    # =====================================================
    # QUANTIDADE DE COMPRA
    # =====================================================
    {
        "ordem": 6,
        "tipo": "eval",
        "coluna": "qtd_compra",
        "formula": "(cobertura - dias_saldo) * consumo_dia",
        "descricao": "Necessidade calculada",
    },
    # =====================================================
    # DECISÃO FINAL DE COMPRA
    # =====================================================
    {
        "ordem": 7,
        "tipo": "select",
        "coluna": "decisao_compra",
        "descricao": "Aplicação de lote mínimo e múltiplo",
        "regras": [
            {"quando": "qtd_compra <= 0", "resultado": "0"},
            {"quando": "qtd_compra < lote_min", "resultado": "lote_min"},
        ],
        "default": (
            "lote_min + "
            "("
            "ceil("
            "(qtd_compra - lote_min) "
            "/ lote_mult"
            ") * lote_mult"
            ")"
        ),
    },
]


# =========================================================
# EXECUTOR DE EXPRESSÕES
# =========================================================


def executar_expressao(df, formula):
    """
    Executa expressão usando eval Python
    com Series pandas vetorizadas
    """

    contexto = {**FUNCOES, **{col: df[col] for col in df.columns}}

    return eval(formula, {"__builtins__": {}}, contexto)


# =========================================================
# EXECUTOR PRINCIPAL
# =========================================================

print("\n================ EXECUÇÃO ================\n")

for regra in sorted(REGRAS, key=lambda x: x["ordem"]):

    inicio = time.time()

    tipo = regra["tipo"]

    coluna = regra["coluna"]

    print(f"\n[{regra['ordem']}] " f"{coluna} " f"({tipo})")

    print(f"Descrição: " f"{regra.get('descricao', '-')}")

    try:

        # =================================================
        # EVAL
        # =================================================

        if tipo == "eval":

            df[coluna] = executar_expressao(df, regra["formula"])

        # =================================================
        # WHERE
        # =================================================

        elif tipo == "where":

            condicao = executar_expressao(df, regra["condicao"])

            verdadeiro = executar_expressao(df, regra["verdadeiro"])

            falso = executar_expressao(df, regra["falso"])

            df[coluna] = np.where(condicao, verdadeiro, falso)

        # =================================================
        # SELECT
        # =================================================

        elif tipo == "select":

            condicoes = []

            valores = []

            for r in regra["regras"]:

                condicoes.append(executar_expressao(df, r["quando"]))

                valores.append(executar_expressao(df, r["resultado"]))

            default = executar_expressao(df, regra["default"])

            df[coluna] = np.select(condicoes, valores, default=default)

        # =================================================
        # TIPO INVÁLIDO
        # =================================================

        else:

            raise Exception(f"Tipo inválido: {tipo}")

        fim = time.time()

        print(f"OK " f"({fim - inicio:.4f}s)")

    except Exception as e:

        print(f"\nERRO na regra " f"[{coluna}]")

        print(str(e))

        break


# =========================================================
# LIMPEZA FINAL
# =========================================================

df.replace([np.inf, -np.inf], np.nan, inplace=True)


# =========================================================
# RESULTADO FINAL
# =========================================================

print("\n================ RESULTADO ================\n")

print(df)
