# Atualiza dados
from app.services.pipeline import coletar_dados
from app.settings import ANALISES
import pickle
import sys
import os
from time import perf_counter

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# if BASE_DIR not in sys.path:
#     sys.path.insert(0, BASE_DIR)


# username = "felipe.cruz"
# password = "#Gladoscruz.9851"

# for analise in ANALISES:
#     dfs = coletar_dados(username, password, analise)
#     with open(f"snapshot_{analise}.pkl", "wb") as f:
#         pickle.dump(dfs, f)
#     print(f"Snapshot salvo para {analise}.")


# Gerar apoio
import pickle
from pathlib import Path
import pandas as pd

analise = "Compra est NEC conf"
dfs = {}
with open(f"snapshot_{analise}.pkl", "rb") as f:
    dfs = pickle.load(f)
print(f"Snapshot carregado para {analise}.")
print(dfs.keys())


from os import sep

apoio_comp = dfs.get("apoio_compras").copy()

# =========================
# Busca histórico de consumo quarto mes completo
# =========================
from app.services.processor import sanitizar_dataframe
from datetime import datetime
from dateutil.relativedelta import relativedelta

data = datetime.now() - relativedelta(months=4)
mes = data.month
ano = data.year
arquivo_apont = Path(f"apont-{ano}-{mes:02d}.csv")
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
    "CSV/apoio.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig"
)

conf = dfs.get("conf").copy()
conf.to_csv("CSV/conf.csv", index=False, sep=";", encoding="utf-8-sig")


# Gerar apoio
import pickle
from pathlib import Path
import pandas as pd

analise = "Compra est NEC conf"
dfs = {}
with open(f"snapshot_{analise}.pkl", "rb") as f:
    dfs = pickle.load(f)
print(f"Snapshot carregado para {analise}.")
print(dfs.keys())


from os import sep

apoio_comp = dfs.get("apoio_compras").copy()

# =========================
# Busca histórico de consumo quarto mes completo
# =========================
from app.services.processor import sanitizar_dataframe
from datetime import datetime
from dateutil.relativedelta import relativedelta

data = datetime.now() - relativedelta(months=4)
mes = data.month
ano = data.year
arquivo_apont = Path(f"apont-{ano}-{mes:02d}.csv")
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
    "CSV/apoio.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig"
)

conf = dfs.get("conf").copy()
conf.to_csv("CSV/conf.csv", index=False, sep=";", encoding="utf-8-sig")

# Tratar dados de entrega

import pandas as pd

# Caminho do arquivo
caminho = r"C:\Users\engli\OneDrive\Área de Trabalho\Analise_compras\CSV\conf.csv"


def tratar_csv():
    # ============================================================
    # LEITURA
    # ============================================================
    df = pd.read_csv(caminho, sep=None, engine="python")

    # Referência das colunas
    col_a = df.columns[0]  # Coluna A -> Item
    col_d = df.columns[3]  # Coluna D
    col_f = df.columns[5]  # Coluna F -> Data
    col_l = df.columns[11]  # Coluna L

    # ============================================================
    # 1) MANTÉM APENAS D == 11
    # ============================================================
    df = df[df[col_d].astype(str).str.strip() == "11"]
    df = df[df[col_l].notna() & (df[col_l].astype(str).str.strip() != "")]

    # ============================================================
    # 2) CONVERTE A COLUNA F PARA DATA
    # ============================================================
    df[col_f] = pd.to_datetime(df[col_f], errors="coerce", dayfirst=True)

    # ============================================================
    # 3) REMOVE LINHAS SEM DATA VÁLIDA
    # ============================================================
    df = df[df[col_f].notna()]

    # Segurança extra:
    # remove valores que viraram NaT após conversão
    df = df.dropna(subset=[col_f])

    # ============================================================
    # 4) ORDENA PELOS MAIS RECENTES
    # ============================================================
    df = df.sort_values(by=col_f, ascending=False)

    # ============================================================
    # 5) MANTÉM SOMENTE OS 5 MAIS RECENTES POR ITEM
    # ============================================================
    df = df.groupby(col_a, group_keys=False).head(5)

    # ============================================================
    # 6) ORDENAÇÃO FINAL
    # ============================================================
    df = df.sort_values(by=[col_a, col_f], ascending=[True, False])

    # ============================================================
    # 7) SALVA O RESULTADO
    # ============================================================
    df.to_csv(caminho, index=False, sep=";")

    print("Arquivo tratado com sucesso.")


tratar_csv()
