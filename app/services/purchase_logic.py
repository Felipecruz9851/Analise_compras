import pandas as pd
import numpy as np
from datetime import date, timedelta
from app.settings import carregar_feriados
from pandas.tseries.offsets import CustomBusinessDay


def compra_necessidade(dfs):
    feriados = carregar_feriados()
    df = dfs.get("apoio_compras")
    # Normalizar formatação numérica (BR -> US) para TODAS as colunas
    for c in df.columns:
        df[c] = df[c].str.replace(".", "").str.replace(",", ".")

    colunas_para_normalizar = [
        "Neces",
        "Estoque Padrão",
        "Lote Mínimo",
        "Dispon",
        "Lote Econom",
        "Estoque Produção",
        "OC",
        "Valor Unitário",
    ]

    for col in colunas_para_normalizar:
        df[col] = df[col].astype(float)

    df["Falta"] = df["Neces"] - (
        df["Estoque Produção"] + df["Estoque Padrão"] + df["OC"]
    )
    df[["Lote Mínimo", "Lote Econom"]] = df[["Lote Mínimo", "Lote Econom"]].replace(
        0, 1
    )
    df["Decis Compras"] = np.where(
        df["Falta"] <= 0,
        0,
        np.where(
            df["Falta"] <= df["Lote Mínimo"],
            df["Lote Mínimo"],
            df["Lote Mínimo"]
            + np.ceil((df["Falta"] - df["Lote Mínimo"]) / df["Lote Econom"])
            * df["Lote Econom"],
        ),
    )

    df["Valor Comprado"] = df["Decis Compras"] * df["Valor Unitário"]

    # força conversão pra número (o que não virar número vira NaN)
    df["Prazo Fornecedor"] = pd.to_numeric(df["Prazo Fornecedor"], errors="coerce")

    # opcional: transforma NaN em 0 (ou outro valor que faça sentido)
    df["Prazo Fornecedor"] = df["Prazo Fornecedor"].fillna(0).astype(int)

    # cálculo da data
    df["Data OC"] = pd.to_datetime("today").normalize() + pd.to_timedelta(
        df["Prazo Fornecedor"], unit="D"
    )

    # converte feriados corretamente
    feriados_pd = pd.to_datetime(feriados)

    bd = CustomBusinessDay(holidays=feriados_pd)

    # ajuste pro próximo dia útil
    df["Data OC"] = df["Data OC"].where(
        (df["Data OC"].dt.weekday < 5) & (~df["Data OC"].isin(feriados_pd)),
        df["Data OC"] + bd,
    )

    df = df.drop(columns=["Ponto", "Dispon"])
    colunas_desejadas = [
        "Item",
        "Descrição",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "Saldo Virtual",
        "Decis Compras",
        "Valor Comprado",
        "Data OC",
        "Lote Mínimo",
        "Lote Econom",
        "Neces",
        "Estoque Padrão",
        "Estoque Produção",
        "Valor Unitário",
        "OC",
        "Valor Estoque",
        "Média Diária",
        "Observação",
        "Última Data Entrada",
        "Última Data Saída",
        "Família",
        "Falta",
    ]
    df["Data OC"] = df["Data OC"].dt.strftime("%d/%m/%Y")

    # mantém só as que existem
    df = df[[col for col in colunas_desejadas if col in df.columns]]

    df = df.round(2)

    return df


def calcular(analise, dfs):
    """
    Recebe o dicionário dfs = {"apoio_compras": df}
    e retorna UM ÚNICO DataFrame (para o pipeline gerar o JSON)
    """

    if dfs is None:
        raise ValueError("Grupo 'apoio_compras' não encontrado no dicionário dfs")

    if analise == "compra por necessidade":
        analise_compra = compra_necessidade(dfs)
    else:
        raise "dados insuficientes"

    return analise_compra
