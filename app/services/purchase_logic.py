import pandas as pd
from bs4 import BeautifulSoup
import time
import numpy as np


def compra_necessidade(df=None):

    for c in df.columns:
        df[c] = df[c].str.replace(".", "")
        df[c] = df[c].str.replace(",", ".")

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

    # Aplicar a transformação em todas as colunas da lista
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

    coluna = df.pop("Falta")
    df.insert(10, "Falta", coluna)
    coluna = df.pop("Decis Compras")
    df.insert(11, "Decis Compras", coluna)
    coluna = df.pop("Valor Comprado")
    df.insert(12, "Valor Comprado", coluna)
    coluna = df.pop("Lote Mínimo")
    df.insert(13, "Lote Mínimo", coluna)
    coluna = df.pop("Lote Econom")
    df.insert(14, "Lote Econom", coluna)

    df = df.drop(columns=["Ponto", "Dispon"])
    df = df.round(2)
    return df


def calcular(analise, df):
    if analise == "compra por necessidade":
        df = compra_necessidade(df)

    return df
