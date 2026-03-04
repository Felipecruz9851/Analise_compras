from pydoc import html
import pandas as pd
import pandas as pd
from bs4 import BeautifulSoup
import time
from app.settings import dict_fam


def extract_table(html: str) -> pd.DataFrame:
    data_ref = time.strftime("%Y-%m")
    print(data_ref)

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
    print("TIPO:", type(dict_fam))
    print("EXEMPLO:", list(dict_fam.items())[:3])
    df["Família"] = df["Item"].map(dict_fam)
    df = df.fillna("")

    return df
