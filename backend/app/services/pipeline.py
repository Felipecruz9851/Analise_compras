from datetime import datetime
import uuid
from app.services.extractor import Extractor
from app.services.processor import juntar_tabelas
from app.services.purchase_logic import calcular, calcular_com_apoio_30
from app import settings
import pandas as pd
import pickle

from time import perf_counter


def coletar_dados(username, password, analise):

    inicio_total = perf_counter()

    if username == "":

    ##### CARREGA SNAPSHOT #######
        dfs = {}
        pkl_path = settings.SNAPSHOTS_DIR / f"snapshot_{analise}.pkl"
        if not pkl_path.exists():
            pkl_path = settings.BASE_DIR / f"snapshot_{analise}.pkl"
        with open(pkl_path, "rb") as f:
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

        # Salva df 'apont' em arquivo
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        data = datetime.now() - relativedelta(months=4)
        mes = data.month
        ano = data.year
        if "apont" in dfs:
            apont_path = settings.DATA_DIR / f"apont-{ano}-{mes:02d}.csv"
            dfs["apont"].to_csv(apont_path, index=False, encoding="utf-8-sig", sep=";")
            print(f"DataFrame 'apont' salvo em {apont_path}.")

    return dfs


def executar_pipeline(username, password, analise):

    inicio = perf_counter()

    dfs = coletar_dados(username, password, analise)

    df = calcular_com_apoio_30(analise, dfs)
    df = df.fillna("")

    duracao = perf_counter() - inicio
    print(f"Pipeline executado em {duracao:.2f} segundos")
    # insere a ID
    if "__rowId" not in df.columns:
        import uuid

        df["__rowId"] = [str(uuid.uuid4()) for _ in range(len(df))]

    # Converter para lista de dicionários (otimizado)
    return df.to_dict(orient="records")
