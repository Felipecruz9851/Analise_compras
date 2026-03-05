import pandas as pd
from bs4 import BeautifulSoup
import time
import numpy as np


def compra_necessidade(df=None):

    # Lista das colunas que deseja normalizar
    colunas_para_normalizar = [
        "Neces",
        "Estoque Padrão",
        "Lote Mínimo",
        "Dispon",
        "Lote Econom",
    ]

    # Aplicar a transformação em todas as colunas da lista
    for col in colunas_para_normalizar:
        df[col] = df[col].str.replace(".", "")
        df[col] = df[col].str.replace(",", ".")
        df[col] = df[col].astype(float)

    df["Falta"] = df["Neces"] - df["Dispon"]

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

    # Mover a coluna para a posição 10 (índice 9)
    coluna = df.pop("Decis Compras")
    df.insert(11, "Decis Compras", coluna)
    coluna = df.pop("Lote Mínimo")
    df.insert(12, "Lote Mínimo", coluna)
    coluna = df.pop("Lote Econom")
    df.insert(13, "Lote Econom", coluna)

    return df


def calcular(analise, df):
    if analise == "compra por necessidade":
        df = compra_necessidade(df)

    return df
