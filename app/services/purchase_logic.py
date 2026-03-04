import pandas as pd
from bs4 import BeautifulSoup
import time
import numpy as np


def compra_necessidade(df=None):

    # Lista das colunas que deseja normalizar
    colunas_para_normalizar = ["neces", "estoque_padrão", "lote_mínimo"]

    # Aplicar a transformação em todas as colunas da lista
    for col in colunas_para_normalizar:
        df[col] = df[col].str.replace(".", "")
        df[col] = df[col].str.replace(",", ".")
        df[col] = df[col].astype(float)
    df["decis_compras"] = df["estoque_padrão"] - df["neces"]
    df["decis_compras"] = np.where(
        df["decis_compras"] <= 0,  # Condição: diferença <= 0
        0,  # Valor se condição verdadeira
        np.ceil(df["decis_compras"] / df["lote_mínimo"])
        * df["lote_mínimo"],  # Valor se condição falsa
    )
    # Mover a coluna para a posição 10 (índice 9)
    coluna = df.pop("decis_compras")  # Remove e guarda a coluna
    df.insert(10, "decis_compras", coluna)  # Insere na posição 10 (índice 9)

    return df


def calcular(analise, df):
    if analise == "compra por necessidade":
        df = compra_necessidade(df)

    return df
