import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple


def juntar_tabelas(
    resultados: List[Tuple[pd.DataFrame, str]],
) -> Dict[str, pd.DataFrame]:
    """
    Recebe lista de (df, grupo) retornada pelos workers e junta DataFrames por grupo.
    """
    grupos = defaultdict(list)

    for df, grupo in resultados:
        grupos[grupo].append(df)

    dfs = {}
    for grupo, lista_dfs in grupos.items():
        if len(lista_dfs) > 1:
            dfs[grupo] = pd.concat(lista_dfs, ignore_index=True)
            print(f"Grupo '{grupo}': {len(lista_dfs)} tabelas unidas")
        else:
            dfs[grupo] = lista_dfs[0]
            print(f"Grupo '{grupo}': tabela única")

    return dfs
