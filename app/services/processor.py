from pydoc import html
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
    if len(rows) < 2:
        raise ValueError("Tabela sem linhas de dados")

    header = [cell.get_text(strip=True) for cell in rows[0].find_all("td")]

    data = [
        [cell.get_text(strip=True) for cell in row.find_all("td")]
        for row in rows[1:]
        if row.find_all("td")
    ]
    df = pd.DataFrame(data, columns=header)

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
            print(f"Falha no grupo {grupo}: {e}")

    dfs = {}
    for grupo, lista_dfs in grupos.items():
        if len(lista_dfs) > 1:
            dfs[grupo] = pd.concat(lista_dfs, ignore_index=True)
            print(f"Grupo '{grupo}': {len(lista_dfs)} tabelas unidas")
        else:
            dfs[grupo] = lista_dfs[0]
            print(f"Grupo '{grupo}': tabela única")

    return dfs  # ← dicionário { "ordens": df }
