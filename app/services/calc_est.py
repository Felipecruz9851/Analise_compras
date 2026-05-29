import time
import pandas as pd
import numpy as np

# =========================================================
# BASE DE DADOS
# =========================================================

df = pd.DataFrame(
    {
        "item": ["A", "B", "C", "D"],
        "estoque": [100, 20, 5, 300],
        "compras": [0, 10, 0, 0],
        "necessidade": [30, 50, 15, 40],
        "consumo_90": [90, 180, 45, 360],
        "cobertura": [45, 30, 20, 60],
    }
)


print("\n================ BASE ================\n")
print(df)


# =========================================================
# REGRAS
# =========================================================
#
# TIPOS:
#
# eval
#   cálculo vetorizado simples
#
# where
#   decisão binária simples
#
# select
#   múltiplas condições/classificação
#
# =========================================================

REGRAS = [
    # =====================================================
    # EVAL
    # =====================================================
    {
        "ordem": 1,
        "ativo": True,
        "tipo": "eval",
        "coluna": "consumo_dia",
        "formula": "consumo_90 / 90",
        "descricao": "Consumo médio diário",
    },
    {
        "ordem": 2,
        "ativo": True,
        "tipo": "eval",
        "coluna": "saldo_virtual",
        "formula": "estoque + compras - necessidade",
        "descricao": "Saldo considerando compras futuras",
    },
    {
        "ordem": 3,
        "ativo": True,
        "tipo": "eval",
        "coluna": "dias_saldo",
        "formula": "saldo_virtual / consumo_dia",
        "descricao": "Quantidade de dias restantes",
    },
    # =====================================================
    # WHERE
    # =====================================================
    {
        "ordem": 4,
        "ativo": True,
        "tipo": "where",
        "coluna": "ponto_pedido",
        "condicao": "dias_saldo < cobertura",
        "verdadeiro": "COMPRAR",
        "falso": "OK",
        "descricao": "Define necessidade de compra",
    },
    # =====================================================
    # SELECT
    # =====================================================
    {
        "ordem": 5,
        "ativo": True,
        "tipo": "select",
        "coluna": "criticidade",
        # IMPORTANTE:
        # O np.select usa o PRIMEIRO match encontrado.
        # Portanto a ordem das condições importa.
        "condicoes": ["dias_saldo <= 5", "dias_saldo <= 15", "dias_saldo <= 30"],
        "valores": ["CRITICO", "ALTO", "MEDIO"],
        "default": "BAIXO",
        "descricao": "Classificação da criticidade",
    },
]


# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================


def validar_coluna(df, coluna):
    """
    Verifica se coluna existe
    """

    if coluna not in df.columns:

        raise Exception(f"Coluna inexistente: {coluna}")


def validar_formula(df, formula):
    """
    Tenta executar expressão
    para validar erros antes
    """

    try:

        df.eval(formula)

    except Exception as e:

        raise Exception(f"Erro na fórmula [{formula}] -> {e}")


# =========================================================
# EXECUTOR
# =========================================================

print("\n================ EXECUÇÃO ================\n")

for regra in sorted(REGRAS, key=lambda x: x["ordem"]):

    # -----------------------------------------------------
    # IGNORA REGRAS INATIVAS
    # -----------------------------------------------------

    if not regra.get("ativo", True):

        continue

    tipo = regra["tipo"]

    coluna = regra["coluna"]

    inicio = time.time()

    print(f"\n[{regra['ordem']}] " f"{coluna} " f"({tipo})")

    print(f"Descrição: " f"{regra.get('descricao', '-')}")

    try:

        # =================================================
        # EVAL
        # =================================================

        if tipo == "eval":

            formula = regra["formula"]

            validar_formula(df, formula)

            df.eval(f"{coluna} = {formula}", inplace=True)

        # =================================================
        # WHERE
        # =================================================

        elif tipo == "where":

            condicao = regra["condicao"]

            validar_formula(df, condicao)

            df[coluna] = np.where(
                df.eval(condicao), regra["verdadeiro"], regra["falso"]
            )

        # =================================================
        # SELECT
        # =================================================

        elif tipo == "select":

            condicoes = []

            for condicao in regra["condicoes"]:

                validar_formula(df, condicao)

                condicoes.append(df.eval(condicao))

            df[coluna] = np.select(
                condicoes, regra["valores"], default=regra["default"]
            )

        # =================================================
        # TIPO DESCONHECIDO
        # =================================================

        else:

            raise Exception(f"Tipo inválido: {tipo}")

        # =================================================
        # TEMPO DE EXECUÇÃO
        # =================================================

        fim = time.time()

        print(f"OK " f"({fim - inicio:.4f}s)")

        print(f"Coluna criada: {coluna}")

    # =====================================================
    # ERRO
    # =====================================================

    except Exception as e:

        print(f"ERRO na regra " f"[{coluna}]")

        print(str(e))

        break


# =========================================================
# RESULTADO FINAL
# =========================================================

print("\n================ RESULTADO ================\n")

print(df)


# =========================================================
# COLUNAS GERADAS
# =========================================================

print("\n================ COLUNAS ================\n")

for c in df.columns:

    print(c)
