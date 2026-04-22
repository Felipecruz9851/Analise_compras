import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple
from tqdm import tqdm


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


def sanitizar_dataframe(df, limite=0.8):
    df = df.copy()

    for col in df.columns:
        serie = df[col].astype(str).str.strip()

        tentativa_data = pd.to_datetime(
            serie, errors="coerce", dayfirst=True, format="%d/%m/%Y"
        )
        if tentativa_data.notna().mean() > limite:
            df[col] = tentativa_data
            continue

        serie_num = serie.str.replace(".", "", regex=False).str.replace(
            ",", ".", regex=False
        )
        tentativa_num = pd.to_numeric(serie_num, errors="coerce")
        if tentativa_num.notna().mean() > limite:
            df[col] = tentativa_num
            continue

        df[col] = serie.replace({"": None})

    return df


def calc_data(dfs):
    print("calculando dados...")

    ## Ajuste Ordens ##
    ordens = sanitizar_dataframe(dfs.get("ordens"))
    ordens = ordens[
        [
            "Cliente",
            "Fábrica",
            "Ordem",
            "Pedido",
            "Item",
            "Saldo",
            "Representante",
            "Entrega Pedido",
            "Data Abertura",
        ]
    ]
    ordens = ordens.rename(columns={"Ordem": "Ordem Prod", "Saldo": "Saldo Prod"})

    colunas = ["Entrega Pedido", "Data Abertura"]
    for col in colunas:
        ordens[col] = (
            ordens[col]
            .astype(str)
            .str.strip()
            .str.replace(r"[^\d]", "", regex=True)
            .pipe(lambda s: pd.to_datetime(s, format="%d%m%Y", errors="coerce"))
        )

    ## Ajuste Consumo ##
    consumo = sanitizar_dataframe(dfs.get("cons"))
    consumo["Item"] = consumo["Item"].str.split("-").str[0].str.strip()
    consumo = consumo[
        [
            "Tipo",
            "Item",
            "Baixa",
            "Consumo",
            "Local Prod.",
            "OP",
            "Familia",
            "Den. Item",
        ]
    ]
    consumo = consumo.rename(columns={"OP": "Ordem Cons"})

    ######## Item Pai ##########
    consumo["item_pai"] = consumo["Ordem Cons"].map(
        ordens.set_index("Ordem Prod")["Item"]
    )

    ######## Merge 1: traz Pedido/Cliente/etc via Ordem Cons ##########
    consumo = consumo.merge(
        ordens[
            [
                "Cliente",
                "Fábrica",
                "Ordem Prod",
                "Pedido",
                "Saldo Prod",
                "Representante",
                "Entrega Pedido",
                "Data Abertura",
            ]
        ].rename(columns={"Ordem Prod": "Ordem", "Saldo Prod": "Saldo"}),
        left_on="Ordem Cons",
        right_on="Ordem",
        how="left",
    )

    ######## Merge 2: Ordem Prod do componente ##########
    ordens_op = ordens[["Item", "Ordem Prod", "Pedido"]].copy()

    consumo_com_pedido = consumo[consumo["Pedido"] > 0]
    consumo_sem_pedido = consumo[consumo["Pedido"] == 0]

    consumo_com_pedido = consumo_com_pedido.merge(
        ordens_op[ordens_op["Pedido"] > 0],
        on=["Item", "Pedido"],
        how="left",
    )

    consumo_sem_pedido = consumo_sem_pedido.merge(
        ordens_op.drop_duplicates("Item")[["Item", "Ordem Prod"]],
        on="Item",
        how="left",
    )

    consumo = pd.concat([consumo_com_pedido, consumo_sem_pedido]).sort_index()

    ######## Ordena as colunas ##########
    consumo = consumo[
        [
            "Tipo",
            "Ordem Prod",
            "Item",
            "Consumo",
            "Ordem Cons",
            "item_pai",
            "Saldo",
            "Pedido",
            "Representante",
            "Entrega Pedido",
            "Local Prod.",
            "Familia",
            "Cliente",
            "Fábrica",
            "Ordem",
            "Data Abertura",
            "Baixa",
            "Den. Item",
        ]
    ]

    ######## Calculos Baseados em estoque ##########
    estoque = sanitizar_dataframe(dfs.get("estoque"))
    consumo["estoque"] = (
        consumo["Item"].map(estoque.groupby("Item")["Qtde."].sum()).fillna(0)
    )

    ######## Propagação dos atributos da raiz ##########

    CAMPOS_RAIZ = [
        "Cliente",
        "Fábrica",
        "Pedido",
        "Representante",
        "Entrega Pedido",
        "Data Abertura",
        "Saldo",
        "Baixa",
    ]
    CAMPOS_RAIZ_COMPLETO = ["Item Final"] + CAMPOS_RAIZ

    itens_existentes = set(consumo["Item"].unique())
    raizes = set(consumo["item_pai"].dropna()) - itens_existentes

    # Nível 0: item_pai aqui É o produto final (raiz real)
    cache_raiz = {}
    for _, row in (
        consumo[consumo["item_pai"].isin(raizes)]
        .drop_duplicates("Ordem Cons")
        .iterrows()
    ):
        cache_raiz[row["Ordem Cons"]] = {
            "Item Final": row["item_pai"],
            **row[CAMPOS_RAIZ].to_dict(),
        }

    # Mapa Ordem Prod → [(Ordem Cons, Pedido_Ordem, Pedido_Contexto)]
    mapa_raw = (
        ordens[["Ordem Prod", "Item", "Pedido"]]
        .rename(columns={"Pedido": "Pedido_Ordem"})
        .merge(
            consumo[["Item", "Ordem Cons", "Pedido"]].drop_duplicates(
                ["Item", "Ordem Cons"]
            ),
            on="Item",
        )
    )

    mapa_op_para_pais = {}
    for _, row in mapa_raw.iterrows():
        op = row["Ordem Prod"]
        if op not in mapa_op_para_pais:
            mapa_op_para_pais[op] = []
        mapa_op_para_pais[op].append(
            (row["Ordem Cons"], row["Pedido_Ordem"], row["Pedido"])
        )

    def achar_pai_no_cache(ordem_cons_filho, pedido_filho):
        pais = mapa_op_para_pais.get(ordem_cons_filho, [])
        pais_no_cache = [(oc, po, pc) for oc, po, pc in pais if oc in cache_raiz]
        if not pais_no_cache:
            return None
        if len(pais_no_cache) == 1:
            return cache_raiz[pais_no_cache[0][0]]
        match = [(oc, po, pc) for oc, po, pc in pais_no_cache if po == pc]
        if len(match) == 1:
            return cache_raiz[match[0][0]]
        match2 = [(oc, po, pc) for oc, po, pc in pais_no_cache if pc == pedido_filho]
        if match2:
            return cache_raiz[match2[0][0]]
        return cache_raiz[pais_no_cache[0][0]]

    # BFS top-down
    for nivel in range(1, 12):
        pendentes = consumo[~consumo["Ordem Cons"].isin(cache_raiz)].drop_duplicates(
            "Ordem Cons"
        )
        novos = 0
        for _, row in tqdm(
            pendentes.iterrows(),
            total=len(pendentes),
            desc=f"Nível {nivel}",
            unit="ordem",
        ):
            resultado = achar_pai_no_cache(row["Ordem Cons"], row["Pedido"])
            if resultado:
                cache_raiz[row["Ordem Cons"]] = resultado
                novos += 1
        print(f"Nível {nivel}: {novos} novas entradas resolvidas")
        if novos == 0:
            break

    raiz_df = (
        consumo["Ordem Cons"]
        .map(cache_raiz)
        .apply(
            lambda x: (
                x if isinstance(x, dict) else {c: None for c in CAMPOS_RAIZ_COMPLETO}
            )
        )
    )
    raiz_df = pd.DataFrame(raiz_df.tolist(), index=consumo.index)
    raiz_df.columns = [f"raiz_{c}" for c in CAMPOS_RAIZ_COMPLETO]
    consumo = pd.concat([consumo, raiz_df], axis=1)
    return consumo
