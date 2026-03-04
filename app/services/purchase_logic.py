import pandas as pd
from bs4 import BeautifulSoup
import time


def compra_necessidade(df=None):

    # Lista das colunas que deseja normalizar
    colunas_para_normalizar = ["neces", "estoque"]

    # Aplicar a transformação em todas as colunas da lista
    for col in colunas_para_normalizar:
        df[col] = df[col].str.replace(",", ".").astype(float)
    df["Decis Compras"] = df["Estoque Padrão"] - df["Neces"]

    return df


def calcular(analise, df):
    if analise == "compra por necessidade":
        df = compra_necessidade(df)

    return df
