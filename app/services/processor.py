from pydoc import html
from anyio import Path
import pandas as pd
import pandas as pd
from bs4 import BeautifulSoup
import time
from app.settings import dict_fam


def extract_table(html: str) -> pd.DataFrame:
    data_ref = time.strftime("%Y-%m")

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", attrs={"border": "1"})
    if table is None:
        raise ValueError("Tabela de dados não encontrada")

    rows = table.find_all("tr")

    header = [cell.get_text(strip=True) for cell in rows[0].find_all(["td", "th"])]

    data = []
    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        # ignora linhas quebradas
        if len(cols) != len(header):
            continue

        data.append(cols)

    df = pd.DataFrame(data, columns=header)

    # só remove se existir
    if data_ref in df.columns:
        df = df.drop(columns=[data_ref])

    return df


def juntar_tabelas(resultados):
    from collections import defaultdict
    import pandas as pd

    grupos = defaultdict(list)

    for html, familia, grupo in resultados:
        try:
            df = extract_table(html)
            df["Família"] = familia
            grupos[grupo].append(df)
        except Exception as e:
            print(f"Erro ao interpretar tabela: {e}")

    dfs = {}
    for grupo, lista_dfs in grupos.items():
        if len(lista_dfs) > 1:
            dfs[grupo] = pd.concat(lista_dfs, ignore_index=True)
            print(f"Grupo '{grupo}': {len(lista_dfs)} tabelas unidas")
        else:
            dfs[grupo] = lista_dfs[0]
            print(f"Grupo '{grupo}': tabela única")
    for nome, df in dfs.items():
        try:
            df.to_excel(f"{nome}.xlsx", index=False)
        except Exception as e:
            print(f"[ERRO] {nome} -> {type(e).__name__}: {e}")

    return dfs  # ← dicionário { "ordens": df }
