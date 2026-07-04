import re
import pandas as pd
import numpy as np
from datetime import date, timedelta
from app.services.processor import calc_data, sanitizar_dataframe
from app.settings import carregar_feriados, prazo_por_representante
from pandas.tseries.offsets import CustomBusinessDay
import re
from pathlib import Path


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

    # Busca estoque Rejeitado

    est_r = dfs.get("estoque_R").copy()
    print(est_r.columns.to_list())
    est_r = est_r[["Item", "Qtde."]]
    est_r = sanitizar_dataframe(est_r)
    est_r = est_r.groupby("Item")["Qtde."].sum()

    # Insere o valor de estoque rejeitado

    df["Estoque Rejeitado"] = df["Item"].map(est_r).fillna(0)
    
    # --- CÁLCULO COMPRA ---
    df["Falta"] = df["Neces"] - (
        df["Estoque Produção"] + df["Estoque Padrão"] + df["OC"] + df["Estoque Rejeitado"]
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

    import numpy as np

    feriados_np = np.array(feriados_pd, dtype="datetime64[D]")

    datas = df["Data OC"].values.astype("datetime64[D]")

    df["Data OC"] = np.busday_offset(
        datas, offsets=0, roll="forward", holidays=feriados_np
    )

    # =========================
    # RATEIO CORRETO (SEM DUPLICAR CONSUMO)
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

    # =========================
    # RATEIO base
    # =========================

    for _, row_base in df.iterrows():

        item = row_base["Item"]
        saldo = row_base["Decis Compras"]

        # ✅ pula rateio se sem necessidade ou Lote Mínimo != 1
        if saldo <= 0 or row_base["Lote Mínimo"] != 1:
            nova = row_base.to_dict()
            if saldo > 0:
                nova["Decis Compras"] = saldo
                nova["Compra Neces."] = row_base["Decis Compras"]
                nova["Valor Comprado"] = saldo * row_base["Valor Unitário"]
            else:
                nova["Compra Neces."] = 0
            nova["raiz_Item Final"] = None
            nova["raiz_Pedido"] = None
            nova["Entrega pedido"] = None
            nova["Representante"] = None
            resultado.append(nova)
            continue

        consumos = consumo_dict.get(item, [])

        consumos = consumo_dict.get(item, [])

        for cons in consumos:
            if saldo <= 0:
                break

            disponivel = cons.get("Consumo", 0)

            if pd.isna(disponivel) or disponivel <= 0:
                continue

            usado = min(saldo, disponivel)

            #  ABATE o consumo
            cons["Consumo"] -= usado

            nova = row_base.to_dict()
            nova["Decis Compras"] = usado
            nova["Compra Neces."] = row_base["Decis Compras"]
            nova["raiz_Item Final"] = cons.get("raiz_Item Final")
            nova["raiz_Pedido"] = cons.get("raiz_Pedido")
            nova["Entrega pedido"] = cons.get("raiz_Entrega Pedido")
            nova["Representante"] = cons.get("raiz_Representante")

            # 🔧 corrige valor proporcional
            nova["Valor Comprado"] = usado * row_base["Valor Unitário"]

            resultado.append(nova)

            saldo -= usado

        # sobra sem consumo
        if saldo > 0:
            nova = row_base.to_dict()
            nova["Decis Compras"] = saldo
            nova["Compra Neces."] = row_base["Decis Compras"]
            nova["raiz_Item Final"] = None
            nova["raiz_Pedido"] = None
            nova["Valor Comprado"] = saldo * row_base["Valor Unitário"]
            nova["Entrega pedido"] = None
            nova["Representante"] = None

            resultado.append(nova)

    df = pd.DataFrame(resultado)

    # =========================
    # COMPLEMENTO (pós-rateio): se raiz_* faltarem para Decis Compras>0,
    # preencher pela “primeira ordem cons” do mesmo Item.
    # =========================
    if not df.empty:
        # referência: consumo original (sem abatimento)
        df_ref = df_consumo.copy()

        # ordenar por Ordem Cons desc e pegar o primeiro registro por Item
        df_ref_sorted = df_ref.sort_values("Ordem Cons", ascending=False)
        df_ref_top = df_ref_sorted.drop_duplicates("Item", keep="first")

        mapa_top = df_ref_top.set_index("Item").to_dict("index")

        def _fill_if_missing(row):
            if pd.isna(row.get("Decis Compras")) or row.get("Decis Compras") <= 0:
                return row
            item = row.get("Item")
            top = mapa_top.get(item)
            if not top:
                return row

            for k_out, k_in in [
                ("raiz_Item Final", "raiz_Item Final"),
                ("raiz_Pedido", "raiz_Pedido"),
                ("raiz_Representante", "raiz_Representante"),
                ("Entrega pedido", "raiz_Entrega Pedido"),
            ]:
                val = row.get(k_out)
                if pd.isna(val) or val is None or val == "":
                    row[k_out] = top.get(k_in)
            # manter compatibilidade com código existente
            if (
                pd.isna(row.get("Representante"))
                or row.get("Representante") is None
                or row.get("Representante") == ""
            ):
                row["Representante"] = top.get("raiz_Representante")
            return row

        df = df.apply(_fill_if_missing, axis=1)

    df["texto OC"] = (
        "ped - "
        + df["raiz_Pedido"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
        + " | "
        + "it - "
        + df["raiz_Item Final"]
        .fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
    )

    # =========================
    # DATA IDEAL (CONSIDERA ENTRGA DO PEDIDO E DIAS DE EXPEDIÇÃO)
    # =========================

    feriados = carregar_feriados()
    feriados_np = np.array(feriados, dtype="datetime64[D]")

    def calcular_data_util(row, feriados_np):
        data = row["Entrega pedido"]
        prazo = row["prazo"]

        if pd.isna(data):
            return pd.NaT

        if prazo <= 0:
            return data

        try:
            return pd.Timestamp(
                np.busday_offset(
                    np.datetime64(data.date()),
                    -int(prazo),
                    roll="backward",
                    holidays=feriados_np,
                )
            )
        except Exception:
            return pd.NaT

    # --- 1. Garantir datetime ---
    df["Entrega pedido"] = pd.to_datetime(df["Entrega pedido"], errors="coerce")

    # --- 2. Mapear prazos ---
    df["prazo"] = df["Representante"].map(prazo_por_representante).fillna(0)

    df["prazo"] = pd.to_numeric(df["prazo"], errors="coerce").fillna(0)

    # --- 3. Calcular Data Ideal considerando feriados ---
    df["Data Ideal"] = df.apply(
        lambda row: calcular_data_util(row, feriados_np), axis=1
    )

    # --- 4. Limpeza ---
    df.drop(columns="prazo", inplace=True)

    # --- 5. Filtro mármore ---

    if not df.empty and "Família" in df.columns:

        # Mapa (Item, raiz_Pedido) → raiz_fábrica a partir do df_consumo
        fab_map = (
            df_consumo.dropna(subset=["raiz_Fábrica"])
            .drop_duplicates(subset=["Item", "raiz_Pedido"])
            .set_index(["Item", "raiz_Pedido"])["raiz_Fábrica"]
            .to_dict()
        )

        hoje = pd.Timestamp.today().normalize()
        limite_data = hoje + pd.Timedelta(days=28)

        mask_vrg = df["Família"] == "VRG"

        def _criterios_vrg(row):
            # Critério 1: Data Ideal <= hoje + 28 dias corridos
            data_ideal = pd.to_datetime(row.get("Data Ideal"), errors="coerce")
            c1 = pd.notna(data_ideal) and data_ideal <= limite_data

            # Critério 2: Representante entre 50 e 100
            try:
                rep = float(row.get("Representante") or "nan")
                c2 = 50 <= rep <= 100 or rep == 0
            except (ValueError, TypeError):
                c2 = False

            # Critério 3: raiz_Fábrica != "UL-ALMOX05"
            chave = (row.get("Item"), row.get("raiz_Pedido"))
            fabrica = fab_map.get(chave)
            c3 = pd.notna(fabrica) and fabrica != "UL-ALMOX05"

            return c1 or c2 or c3

        nenhum_criterio = mask_vrg & ~df.apply(_criterios_vrg, axis=1)

        df.loc[nenhum_criterio, "Decis Compras"] = 0
        df.loc[nenhum_criterio, "Valor Comprado"] = 0

    # =========================
    # Busca histórico de consumo quarto mes completo
    # =========================

    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    data = datetime.now() - relativedelta(months=4)
    mes = data.month
    ano = data.year
    arquivo_apont = Path(f"apont-{ano}-{mes:02d}.csv")
    df_apont = pd.read_csv(arquivo_apont, sep=";", encoding="utf-8-sig")
    df_apont = sanitizar_dataframe(df_apont)
    df_apont = df_apont[["Item", "Qtde."]].groupby("Item", as_index=False).sum()

    nome_col = f"{ano}-{mes:02d}"

    df[nome_col] = df["Item"].map(df_apont.set_index("Item")["Qtde."]).fillna(0)

    if nome_col in df.columns:
        col = df.pop(nome_col)
        df.insert(2, nome_col, col)
    else:
        df.insert(2, nome_col, pd.NA)

    # =========================
    # FINAL
    # =========================

    df = df.drop(columns=["Ponto", "Dispon"], errors="ignore")

    colunas_mes = [col for col in df.columns if re.match(r"^\d{4}-\d{2}$", col)]

    colunas_desejadas = [
        "Item",
        "Descrição",
        *colunas_mes,
        "Neces",
        "Estoque Padrão",
        "Estoque Produção",
        "Decis Compras",
        "Valor Comprado",
        "Compra Neces.",
        "texto OC",
        "Data Ideal",
        "Entrega pedido",
        "Representante",
        "Saldo Virtual",
        "Data OC",
        "Lote Mínimo",
        "Lote Econom",
        "Valor Unitário",
        "OC",
        "Valor Estoque",
        "Média Diária",
        "Observação",
        "Última Data Entrada",
        "Última Data Saída",
        "raiz_Item Final",
        "raiz_Pedido",
        "Estoque Rejeitado",
        "Família",
        "Falta",
    ]

    df["Data OC"] = df["Data OC"].dt.strftime("%d/%m/%Y")

    df = df[[col for col in colunas_desejadas if col in df.columns]]

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].round(2)

    for col in df.select_dtypes(include=["datetime64[ns]"]):
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    df = df.where(pd.notnull(df), None)

    return df


def compra_estoque_nec_conf(dfs):
    import pandas as pd
    import numpy as np
    from pandas.tseries.offsets import CustomBusinessDay
    import re

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

    # =========================
    # Busca histórico de consumo quarto mes completo
    # =========================

    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    data = datetime.now() - relativedelta(months=4)
    mes = data.month
    ano = data.year
    arquivo_apont = Path(f"apont-{ano}-{mes:02d}.csv")
    df_apont = pd.read_csv(arquivo_apont, sep=";", encoding="utf-8-sig")
    df_apont = sanitizar_dataframe(df_apont)
    df_apont = df_apont[["Item", "Qtde."]].groupby("Item", as_index=False).sum()

    nome_col = f"{ano}-{mes:02d}"

    df[nome_col] = df["Item"].map(df_apont.set_index("Item")["Qtde."]).fillna(0)

    if nome_col in df.columns:
        col = df.pop(nome_col)
        df.insert(2, nome_col, col)
    else:
        df.insert(2, nome_col, pd.NA)
    ##########################################################################

    ##########################################################################

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

    import numpy as np

    feriados_np = np.array(feriados_pd, dtype="datetime64[D]")

    datas = df["Data OC"].values.astype("datetime64[D]")

    df["Data OC"] = np.busday_offset(
        datas, offsets=0, roll="forward", holidays=feriados_np
    )

    # =========================
    # FINAL
    # =========================

    df = df.drop(columns=["Ponto", "Dispon"], errors="ignore")

    colunas_mes = [col for col in df.columns if re.match(r"^\d{4}-\d{2}$", col)]
    print(colunas_mes)
    colunas_desejadas = [
        "Item",
        "Descrição",
        *colunas_mes,
        "Neces",
        "Estoque Padrão",
        "Estoque Produção",
        "Decis Compras",
        "Valor Comprado",
        "Saldo Virtual",
        "Data OC",
        "Lote Mínimo",
        "Lote Econom",
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

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].round(2)

    for col in df.select_dtypes(include=["datetime64[ns]"]):
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    df = df.where(pd.notnull(df), None)
    # df.to_excel("debug_compra_estoque_nec_conf.xlsx", index=False)
    print(
        "DataFrame final gerado para análise 'Compra est NEC conf' com colunas:",
        df.columns,
    )
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
    elif analise == "Compra est NEC conf":
        analise_compra = compra_estoque_nec_conf(dfs)

    else:
        raise NotImplementedError(
            "Análise 'Compra est NEC conf' ainda não implementada"
        )
    return analise_compra
