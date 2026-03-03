import pandas as pd

def processar(dados):
    df = pd.DataFrame(dados)
    df["dias_estoque"] = df["estoque"] / df["consumo_dia"]
    return df