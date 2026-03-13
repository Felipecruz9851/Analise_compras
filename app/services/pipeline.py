from app.services.extractor import Extractor
from app.services.processor import juntar_tabelas
from app.services.purchase_logic import calcular
import pandas as pd


def executar_pipeline(username, password, analise):

    extractor = Extractor(username, password)
    print("Extractor criado com sucesso!")

    html_resultados = extractor.executar(analise)
    print("Dados coletados com sucesso!")

    dfs = juntar_tabelas(html_resultados)  # ← dicionário com "ordens"
    print("Dicionário dfs gerado com grupos:", list(dfs.keys()))

    df = calcular(analise, dfs)  # ← calcular recebe dict e devolve df único

    df = df.fillna("")
    return df.to_dict(orient="records")  # ← JSON idêntico ao que era antes
