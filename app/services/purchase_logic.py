import pandas as pd
import numpy as np
from datetime import date, timedelta
from app.services.processor import calc_data
from app.settings import carregar_feriados
from pandas.tseries.offsets import CustomBusinessDay


def compra_necessidade(dfs):
    import pandas as pd
    import numpy as np
    from pandas.tseries.offsets import CustomBusinessDay

    feriados = carregar_feriados()
    df = dfs.get("apoio_compras").copy()

    # --- NORMALIZAÇÃO ---
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = (
                df[c]
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )

    colunas_para_normalizar = [
        "Neces",
        "Estoque Padrão",
        "Lote Mínimo",
        "Dispon",
        "Lote Econom",
        "Estoque Produção",
        "OC",
        "Valor Unitário",
    ]

    for col in colunas_para_normalizar:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- CÁLCULO COMPRA ---
    df["Falta"] = df["Neces"] - (
        df["Estoque Produção"] + df["Estoque Padrão"] + df["OC"]
    )

    df[["Lote Mínimo", "Lote Econom"]] = df[["Lote Mínimo", "Lote Econom"]].replace(
        0, 1
    )

    df["Decis Compras"] = np.where(
        df["Falta"] <= 0,
        0,
        np.where(
            df["Falta"] <= df["Lote Mínimo"],
            df["Lote Mínimo"],
            df["Lote Mínimo"]
            + np.ceil((df["Falta"] - df["Lote Mínimo"]) / df["Lote Econom"])
            * df["Lote Econom"],
        ),
    )

    df["Valor Comprado"] = df["Decis Compras"] * df["Valor Unitário"]

    # --- DATA OC ---
    df["Prazo Fornecedor"] = (
        pd.to_numeric(df["Prazo Fornecedor"], errors="coerce").fillna(0).astype(int)
    )

    df["Data OC"] = pd.to_datetime("today").normalize() + pd.to_timedelta(
        df["Prazo Fornecedor"], unit="D"
    )

    feriados_pd = pd.to_datetime(feriados)
    bd = CustomBusinessDay(holidays=feriados_pd)

    df["Data OC"] = df["Data OC"].where(
        (df["Data OC"].dt.weekday < 5) & (~df["Data OC"].isin(feriados_pd)),
        df["Data OC"] + bd,
    )

    # =========================
    # 🔥 RATEIO CORRETO (SEM DUPLICAR CONSUMO)
    # =========================

    df_consumo = calc_data(dfs).copy()
    # =========================
    # TRATAMENTO DE VARIOS ITENS PRODUZIDOS NO MESMO ITEM FINAL (RAIZ)
    # =========================

    chaves = ["Item", "raiz_Item Final", "raiz_Pedido"]

    df_consumo = df_consumo.groupby(chaves, as_index=False).agg(
        {
            "Consumo": "sum",
            **{
                col: "first"
                for col in df_consumo.columns
                if col not in chaves + ["Consumo"]
            },
        }
    )

    ###########################

    # 🔑 cria estrutura mutável de consumo (estado compartilhado)
    consumo_dict = {
        item: grupo.sort_values("Ordem Cons", ascending=False).to_dict("records")
        for item, grupo in df_consumo.groupby("Item")
    }

    resultado = []

    for _, row_base in df.iterrows():
        item = row_base["Item"]
        saldo = row_base["Decis Compras"]

        consumos = consumo_dict.get(item, [])

        for cons in consumos:
            if saldo <= 0:
                break

            disponivel = cons.get("Consumo", 0)

            if pd.isna(disponivel) or disponivel <= 0:
                continue

            usado = min(saldo, disponivel)

            # 🔥 ABATE o consumo (isso resolve a duplicação)
            cons["Consumo"] -= usado

            nova = row_base.to_dict()
            nova["Decis Compras"] = usado
            nova["Compra Neces."] = row_base["Decis Compras"]

            nova["raiz_Item Final"] = cons.get("raiz_Item Final")
            nova["raiz_Pedido"] = cons.get("raiz_Pedido")

            # 🔧 corrige valor proporcional
            nova["Valor Comprado"] = usado * row_base["Valor Unitário"]

            resultado.append(nova)

            saldo -= usado

        # sobra sem consumo
        if saldo > 0:
            nova = row_base.to_dict()
            nova["Decis Compras"] = saldo
            nova["Compra Neces."] = saldo
            nova["raiz_Item Final"] = None
            nova["raiz_Pedido"] = None
            nova["Valor Comprado"] = saldo * row_base["Valor Unitário"]

            resultado.append(nova)

    df = pd.DataFrame(resultado)

    # =========================
    # 🔚 FINAL
    # =========================

    df = df.drop(columns=["Ponto", "Dispon"], errors="ignore")

    colunas_desejadas = [
        "Item",
        "Descrição",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "raiz_Item Final",
        "raiz_Pedido",
        "Compra Neces.",
        "Decis Compras",
        "Valor Comprado",
        "Saldo Virtual",
        "Data OC",
        "Lote Mínimo",
        "Lote Econom",
        "Neces",
        "Estoque Padrão",
        "Estoque Produção",
        "Valor Unitário",
        "OC",
        "Valor Estoque",
        "Média Diária",
        "Observação",
        "Última Data Entrada",
        "Última Data Saída",
        "Família",
        "Falta",
    ]

    df["Data OC"] = df["Data OC"].dt.strftime("%d/%m/%Y")

    df = df[[col for col in colunas_desejadas if col in df.columns]]

    df = df.round(2)

    return df


def calcular(analise, dfs):
    """
    Recebe o dicionário dfs = {"apoio_compras": df}
    e retorna UM ÚNICO DataFrame (para o pipeline gerar o JSON)
    """

    if dfs is None:
        raise ValueError("Grupo 'apoio_compras' não encontrado no dicionário dfs")

    if analise == "compra por necessidade":
        analise_compra = compra_necessidade(dfs)
    else:
        raise "dados insuficientes"

    return analise_compra
