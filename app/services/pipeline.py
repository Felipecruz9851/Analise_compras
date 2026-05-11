import uuid
from app.services.extractor import Extractor
from app.services.processor import juntar_tabelas
from app.services.purchase_logic import calcular
import pandas as pd
import pickle

from time import perf_counter


def coletar_dados(username, password, analise):

    inicio_total = perf_counter()

    if username == "":

        #### CARREGA SNAPSHOT #######
        dfs = {}
        with open(f"snapshot_{analise}.pkl", "rb") as f:
            dfs = pickle.load(f)
        print(f"Snapshot carregado para {analise}.")
    #############################

    else:

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
    # insere a ID
    if "__rowId" not in df.columns:
        import uuid

        df["__rowId"] = [str(uuid.uuid4()) for _ in range(len(df))]

    # Converter para lista de dicionários (otimizado)
    return df.to_dict(orient="records")
