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
    dfs = []

    for html, familia in resultados:

        try:
            df = extract_table(html)

            df["Família"] = familia

            if not df.empty:
                dfs.append(df)

        except Exception as e:
            print("Falha ao extrair tabela:", e)

    return pd.concat(dfs, ignore_index=True)
