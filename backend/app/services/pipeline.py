from datetime import datetime
import uuid
from app.services.extractor import Extractor
from app.services.processor import juntar_tabelas
from app.services.purchase_logic import calcular, calcular_com_apoio_30
from app import settings
import pandas as pd
import pickle

from time import perf_counter


def coletar_dados(username: str = "", password: str = "", analise: str = "Geral"):
    """
    Coleta dados brutos completos:
    - Se username=='': carrega o snapshot master (snapshot_Geral.pkl) ou específico da análise.
    - Se username!='': executa o Extractor unificado (coleta dados para necessidade e apoio de compras para todas as famílias).
    """
    inicio_total = perf_counter()

    if username == "":
        ##### CARREGA SNAPSHOT #######
        dfs = {}
        # Prioriza o snapshot master Geral (que contém todas as famílias e necessidade)
        candidatos = [
            settings.SNAPSHOTS_DIR / "snapshot_Geral.pkl",
            settings.SNAPSHOTS_DIR / f"snapshot_{analise}.pkl",
            settings.BASE_DIR / "snapshot_Geral.pkl",
            settings.BASE_DIR / f"snapshot_{analise}.pkl",
        ]

        pkl_path = None
        for cand in candidatos:
            if cand.exists():
                pkl_path = cand
                break

        if pkl_path is None or not pkl_path.exists():
            raise FileNotFoundError(
                f"Nenhum snapshot encontrado em {settings.SNAPSHOTS_DIR}. Execute a geração de dados primeiro."
            )

        with open(pkl_path, "rb") as f:
            dfs = pickle.load(f)
        print(f"Snapshot carregado de {pkl_path.name} para a análise '{analise}'.")
        #############################

    else:
        extractor = Extractor(username, password)
        print("Extractor criado com sucesso!")

        html_resultados = extractor.executar(analise)
        print("Páginas coletadas.")

        duracao_total = perf_counter() - inicio_total
        print(f"Coleta executada em {duracao_total:.2f} segundos")

        dfs = juntar_tabelas(html_resultados)
        print("Dados tratados.")
        print("Dicionário dfs gerado com grupos:", list(dfs.keys()))

        # Salva df 'apont' em arquivo se presente
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


def executar_pipeline(username: str, password: str, analise: str):
    """
    Orquestra o pipeline analítico:
    1. Coleta o conjunto de dados completo (necessidade + todas as famílias).
    2. Delega o cálculo para calcular_com_apoio_30, que filtra as famílias do grupo e calcula.
    3. Atribui rowIds para identificação estável no frontend e retorna os registros.
    """
    inicio = perf_counter()

    dfs = coletar_dados(username, password, analise)

    df = calcular_com_apoio_30(analise, dfs)
    df = df.fillna("")

    duracao = perf_counter() - inicio
    print(f"Pipeline executado em {duracao:.2f} segundos para a análise '{analise}'")

    # insere o ID único para a tabela da interface
    if "__rowId" not in df.columns:
        import uuid

        df["__rowId"] = [str(uuid.uuid4()) for _ in range(len(df))]

    # Converter para lista de dicionários (otimizado)
    return df.to_dict(orient="records")
