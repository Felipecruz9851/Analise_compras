# Atualiza dados
import sys
from pathlib import Path
import pickle
import os
from time import perf_counter
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.pipeline import coletar_dados
from app.services.processor import sanitizar_dataframe
from app.settings import ANALISES, SNAPSHOTS_DIR, DATA_DIR, CSV_DIR, BASE_DIR


def atualizar_snapshots(username="", password=""):
    dfs = coletar_dados(username, password, "Geral")
    if not dfs:
        print("Erro: Dados não atualizados. O sistema retornou uma extração vazia.")
        return
    dest_geral = SNAPSHOTS_DIR / "snapshot_Geral.pkl"
    with open(dest_geral, "wb") as f:
        pickle.dump(dfs, f)
    print(f"Snapshot master salvo em {dest_geral}.")

    dest_nec = SNAPSHOTS_DIR / "snapshot_compra por necessidade.pkl"
    with open(dest_nec, "wb") as f:
        pickle.dump(dfs, f)
    print(f"Snapshot salvo em {dest_nec}.")


def gerar_apoio():
    analise = "compra por necessidade"
    dfs = {}
    pkl_file = SNAPSHOTS_DIR / f"snapshot_{analise}.pkl"
    if not pkl_file.exists():
        pkl_file = BASE_DIR / f"snapshot_{analise}.pkl"
    with open(pkl_file, "rb") as f:
        dfs = pickle.load(f)
    print(f"Snapshot carregado para {analise}.")
    print(dfs.keys())

    apoio_comp = dfs.get("apoio_compras").copy()

    # Busca histórico de consumo quarto mes completo
    data = datetime.now() - relativedelta(months=4)
    mes = data.month
    ano = data.year
    arquivo_apont = DATA_DIR / f"apont-{ano}-{mes:02d}.csv"
    if not arquivo_apont.exists():
        arquivo_apont = BASE_DIR / f"apont-{ano}-{mes:02d}.csv"

    if arquivo_apont.exists():
        df_apont = pd.read_csv(
            arquivo_apont, sep=";", decimal=",", encoding="utf-8-sig", low_memory=False
        )
        df_apont = sanitizar_dataframe(df_apont)
        df_apont = df_apont[["Item", "Qtde."]].groupby("Item", as_index=False).sum()

        nome_col = f"{ano}-{mes:02d}"
        apoio_comp[nome_col] = (
            apoio_comp["Item"].map(df_apont.set_index("Item")["Qtde."]).fillna(0)
        )

        if nome_col in apoio_comp.columns:
            col = apoio_comp.pop(nome_col)
            apoio_comp.insert(2, nome_col, col)
        else:
            apoio_comp.insert(2, nome_col, pd.NA)

        apoio_comp = apoio_comp.reindex(
            columns=apoio_comp.columns.drop("Baixa").tolist() + ["Baixa"]
        )

    apoio_comp.to_csv(
        CSV_DIR / "apoio.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig"
    )

    conf = dfs.get("conf").copy()
    conf.to_csv(CSV_DIR / "conf.csv", index=False, sep=";", encoding="utf-8-sig")


def gerar_apoio_geral():
    analise = "Geral"
    dfs = {}
    pkl_file = SNAPSHOTS_DIR / f"snapshot_{analise}.pkl"
    if not pkl_file.exists():
        pkl_file = BASE_DIR / f"snapshot_{analise}.pkl"
    with open(pkl_file, "rb") as f:
        dfs = pickle.load(f)
    print(f"Snapshot carregado para {analise}.")
    print(dfs.keys())

    apoio_comp = dfs.get("apoio_compras").copy()

    # Busca histórico de consumo quarto mes completo
    data = datetime.now() - relativedelta(months=4)
    mes = data.month
    ano = data.year
    arquivo_apont = DATA_DIR / f"apont-{ano}-{mes:02d}.csv"
    if not arquivo_apont.exists():
        arquivo_apont = BASE_DIR / f"apont-{ano}-{mes:02d}.csv"

    if arquivo_apont.exists():
        df_apont = pd.read_csv(arquivo_apont, sep=";", decimal=",", encoding="utf-8-sig")
        df_apont = sanitizar_dataframe(df_apont)
        df_apont = df_apont[["Item", "Qtde."]].groupby("Item", as_index=False).sum()

        nome_col = f"{ano}-{mes:02d}"
        apoio_comp[nome_col] = (
            apoio_comp["Item"].map(df_apont.set_index("Item")["Qtde."]).fillna(0)
        )

        if nome_col in apoio_comp.columns:
            col = apoio_comp.pop(nome_col)
            apoio_comp.insert(2, nome_col, col)
        else:
            apoio_comp.insert(2, nome_col, pd.NA)

        apoio_comp = apoio_comp.reindex(
            columns=apoio_comp.columns.drop("Baixa").tolist() + ["Baixa"]
        )

    apoio_comp.to_csv(
        CSV_DIR / "apoio.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig"
    )

    conf = dfs.get("conf").copy()
    conf.to_csv(CSV_DIR / "conf.csv", index=False, sep=";", encoding="utf-8-sig")


def tratar_csv():
    caminho = CSV_DIR / "conf.csv"
    if not caminho.exists():
        print(f"Arquivo {caminho} não encontrado para tratamento.")
        return

    df = pd.read_csv(caminho, sep=";")

    col_a = df.columns[0]  # Item
    col_d = df.columns[3]  # Empresa
    col_f = df.columns[5]  # Data
    col_l = df.columns[11]

    # 1) Mantém apenas D == 11
    df = df[df[col_d].astype(str).str.strip() == "11"]
    df = df[df[col_l].notna() & (df[col_l].astype(str).str.strip() != "")]

    # 2) Converte coluna F para data
    df[col_f] = pd.to_datetime(df[col_f], errors="coerce", dayfirst=True)

    # 3) Remove linhas sem data válida
    df = df[df[col_f].notna()].dropna(subset=[col_f])

    # 4) Ordena pelos mais recentes
    df = df.sort_values(by=col_f, ascending=False)

    # 5) Mantém somente os 5 mais recentes por item
    df = df.groupby(col_a, group_keys=False).head(5)

    # 6) Ordenação final
    df = df.sort_values(by=[col_a, col_f], ascending=[True, False])

    # 7) Salva o resultado
    df.to_csv(caminho, index=False, sep=";")
    print("Arquivo conf.csv tratado com sucesso.")


if __name__ == "__main__":
    gerar_apoio()
    gerar_apoio_geral()
    tratar_csv()
