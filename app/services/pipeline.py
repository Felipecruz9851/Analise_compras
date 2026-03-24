from app.services.extractor import Extractor
from app.services.processor import juntar_tabelas
from app.services.purchase_logic import calcular
import pandas as pd

from time import perf_counter


def coletar_dados(username, password, analise):

    inicio_total = perf_counter()

    extractor = Extractor(username, password)
    print("Extractor criado com sucesso!")

    html_resultados = extractor.executar(analise)
    print("Paginas coletadas.")

    duracao_total = perf_counter() - inicio_total
    print(f"Coleta executada em {duracao_total:.2f} segundos")

    dfs = juntar_tabelas(html_resultados)
    print("Dados tratados.")
    print("Dicionário dfs gerado com grupos:", list(dfs.keys()))

    return dfs


def executar_pipeline(username, password, analise):

    inicio = perf_counter()

    dfs = coletar_dados(username, password, analise)

    df = calcular(analise, dfs)
    df = df.fillna("")

    duracao = perf_counter() - inicio
    print(f"Pipeline executado em {duracao:.2f} segundos")

    # Converter para lista de dicionários (otimizado)
    return df.to_dict(orient="records")
