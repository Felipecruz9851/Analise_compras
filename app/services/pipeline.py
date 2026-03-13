from app.services.extractor import Extractor
from app.services.processor import juntar_tabelas
from app.services.purchase_logic import calcular
import pandas as pd


from time import perf_counter


def executar_pipeline(username, password, analise):

    inicio_total = perf_counter()

    extractor = Extractor(username, password)
    print("Extractor criado com sucesso!")

    html_resultados = extractor.executar(analise)

    duracao_total = perf_counter() - inicio_total
    print(f"Coleta executada em {duracao_total:.2f} segundos")

    dfs = juntar_tabelas(html_resultados)
    print("Dicionário dfs gerado com grupos:", list(dfs.keys()))

    df = calcular(analise, dfs)

    df = df.fillna("")

    duracao_total = perf_counter() - inicio_total
    print(f"Pipeline completo executado em {duracao_total:.2f} segundos")

    return df.to_dict(orient="records")
