import pandas as pd
import pandas as pd
from bs4 import BeautifulSoup


def extract_table(html: str) -> pd.DataFrame:
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

    return pd.DataFrame(data, columns=header)
