import re
from datetime import datetime

import numpy as np
import pandas as pd
from app.services.analise_estoque import detectar_meses, processar_analise_compras
from app.services.processor import calc_data, sanitizar_dataframe
from app.settings import BASE_DIR, DATA_DIR, carregar_feriados, prazo_por_representante
from dateutil.relativedelta import relativedelta
from pandas.tseries.offsets import CustomBusinessDay


def compra_necessidade(dfs):
    import numpy as np
    import pandas as pd

    feriados = carregar_feriados()
    df = dfs.get("apoio_compras").copy()

    # --- NORMALIZAÇÃO SEGURA ---
    def _converter_valor_seguro(val):
        if pd.isna(val) or val is None or val == "":
            return 0.0
        if isinstance(val, (int, float, np.number)):
            return float(val)
        s = str(val).strip()
        if not s:
            return 0.0
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except (ValueError, TypeError):
            return 0.0

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
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].map(_converter_valor_seguro)
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    # Busca estoque Rejeitado

    if dfs.get("estoque_R") is None:
        raise ValueError("Grupo 'estoque_R' ausente no dicionário dfs.")
    est_r = dfs.get("estoque_R").copy()
    print(est_r.columns.to_list())
    est_r = est_r[["Item", "Qtde."]]
    est_r = sanitizar_dataframe(est_r)
    est_r = est_r.groupby("Item")["Qtde."].sum()

    # Insere o valor de estoque rejeitado

    df["Estoque Rejeitado"] = df["Item"].map(est_r).fillna(0)

    # --- CÁLCULO COMPRA ---
    df["Falta"] = df["Neces"] - (
        df["Estoque Produção"]
        + df["Estoque Padrão"]
        + df["OC"]
        + df["Estoque Rejeitado"]
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

    # 🔑 OTIMIZAÇÃO 1: Construção de consumo_dict em O(N) com sort global único
    df_consumo_sorted = df_consumo.sort_values("Ordem Cons", ascending=False)
    consumo_dict = {}
    for r in df_consumo_sorted.to_dict("records"):
        it = r["Item"]
        if it not in consumo_dict:
            consumo_dict[it] = []
        consumo_dict[it].append(r)

    # Preparar mapa_top para complemento rápido pós-rateio
    df_ref_top = df_consumo_sorted.drop_duplicates("Item", keep="first")

    # 🔑 OTIMIZAÇÃO 2: Rateio direto com dicionários Python (sem row_base.to_dict() repetido)
    df_records = df.to_dict("records")
    resultado = []

    for row_base in df_records:
        item = row_base["Item"]
        saldo = row_base["Decis Compras"]
        v_unit = row_base["Valor Unitário"]

        # ✅ pula rateio se sem necessidade ou Lote Mínimo != 1
        if saldo <= 0 or row_base["Lote Mínimo"] != 1:
            nova = dict(row_base)
            if saldo > 0:
                nova["Decis Compras"] = saldo
                nova["Compra Neces."] = saldo
                nova["Valor Comprado"] = saldo * v_unit
            else:
                nova["Compra Neces."] = 0
            nova["raiz_Item Final"] = None
            nova["raiz_Pedido"] = None
            nova["Entrega pedido"] = None
            nova["Representante"] = None
            resultado.append(nova)
            continue

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

            nova = dict(row_base)
            nova["Decis Compras"] = usado
            nova["Compra Neces."] = row_base["Decis Compras"]
            nova["raiz_Item Final"] = cons.get("raiz_Item Final")
            nova["raiz_Pedido"] = cons.get("raiz_Pedido")
            nova["Entrega pedido"] = cons.get("raiz_Entrega Pedido")
            nova["Representante"] = cons.get("raiz_Representante")
            nova["Valor Comprado"] = usado * v_unit

            resultado.append(nova)
            saldo -= usado

        # sobra sem consumo
        if saldo > 0:
            nova = dict(row_base)
            nova["Decis Compras"] = saldo
            nova["Compra Neces."] = row_base["Decis Compras"]
            nova["raiz_Item Final"] = None
            nova["raiz_Pedido"] = None
            nova["Valor Comprado"] = saldo * v_unit
            nova["Entrega pedido"] = None
            nova["Representante"] = None
            resultado.append(nova)

    df = pd.DataFrame(resultado)

    # =========================
    # COMPLEMENTO (pós-rateio): se raiz_* faltarem para Decis Compras>0,
    # preencher pela “primeira ordem cons” do mesmo Item.
    # =========================
    if not df.empty:
        mask_decis = (df["Decis Compras"] > 0)
        
        for k_out, k_in in [
            ("raiz_Item Final", "raiz_Item Final"),
            ("raiz_Pedido", "raiz_Pedido"),
            ("raiz_Representante", "raiz_Representante"),
            ("Entrega pedido", "raiz_Entrega Pedido"),
        ]:
            if k_out not in df.columns:
                df[k_out] = None
            serie_top = df_ref_top.set_index("Item")[k_in]
            val_top = df["Item"].map(serie_top)
            mask_empty = mask_decis & (df[k_out].isna() | (df[k_out] == ""))
            df.loc[mask_empty, k_out] = val_top[mask_empty]

        if "Representante" not in df.columns:
            df["Representante"] = None
        serie_rep = df_ref_top.set_index("Item")["raiz_Representante"]
        val_rep = df["Item"].map(serie_rep)
        mask_rep_empty = mask_decis & (df["Representante"].isna() | (df["Representante"] == ""))
        df.loc[mask_rep_empty, "Representante"] = val_rep[mask_rep_empty]

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
    # DATA IDEAL (CONSIDERA ENTREGA DO PEDIDO E DIAS DE EXPEDIÇÃO)
    # =========================

    feriados = carregar_feriados()
    feriados_np = np.array(feriados, dtype="datetime64[D]")

    # --- 1. Garantir datetime e prazos ---
    df["Entrega pedido"] = pd.to_datetime(df["Entrega pedido"], errors="coerce")
    df["prazo"] = df["Representante"].map(prazo_por_representante).fillna(0)
    df["prazo"] = pd.to_numeric(df["prazo"], errors="coerce").fillna(0).astype(int)

    # --- 2. Calcular Data Ideal considerando feriados (vetorizado) ---
    entregas = df["Entrega pedido"]
    prazos = df["prazo"].values
    datas_ideal = pd.Series(index=df.index, dtype="datetime64[ns]")
    mask_valida = entregas.notna()

    if mask_valida.any():
        sub_entregas = entregas[mask_valida]
        sub_prazos = prazos[mask_valida]
        mask_prazo_zero = sub_prazos <= 0
        datas_ideal.loc[sub_entregas[mask_prazo_zero].index] = sub_entregas[mask_prazo_zero]

        mask_prazo_pos = ~mask_prazo_zero
        if mask_prazo_pos.any():
            pos_indices = sub_entregas[mask_prazo_pos].index
            pos_datas_np = sub_entregas[mask_prazo_pos].dt.date.values.astype("datetime64[D]")
            pos_offsets = -sub_prazos[mask_prazo_pos]
            offset_dates = np.busday_offset(
                pos_datas_np,
                pos_offsets,
                roll="backward",
                holidays=feriados_np
            )
            datas_ideal.loc[pos_indices] = pd.to_datetime(offset_dates)

    df["Data Ideal"] = datas_ideal
    df.drop(columns="prazo", inplace=True)

    # --- 3. Filtro mármore (VRG) vetorizado ---
    if not df.empty and "Família" in df.columns:
        hoje = pd.Timestamp.today().normalize()
        limite_data = hoje + pd.Timedelta(days=28)
        mask_vrg = df["Família"] == "VRG"

        if mask_vrg.any():
            dt_ideal = pd.to_datetime(df["Data Ideal"], errors="coerce")
            c1 = dt_ideal.notna() & (dt_ideal <= limite_data)

            rep_num = pd.to_numeric(df["Representante"], errors="coerce")
            c2 = ((rep_num >= 50) & (rep_num <= 100)) | (rep_num == 0)

            fab_map = (
                df_consumo.dropna(subset=["raiz_Fábrica"])
                .drop_duplicates(subset=["Item", "raiz_Pedido"])
                .set_index(["Item", "raiz_Pedido"])["raiz_Fábrica"]
                .to_dict()
            )
            tuplas_chave = list(zip(df["Item"], df["raiz_Pedido"]))
            fabricas = [fab_map.get(k) for k in tuplas_chave]
            c3 = pd.Series([f is not None and pd.notna(f) and f != "UL-ALMOX05" for f in fabricas], index=df.index)

            criterio_ok = c1 | c2 | c3
            nenhum_criterio = mask_vrg & (~criterio_ok)

            df.loc[nenhum_criterio, "Decis Compras"] = 0
            df.loc[nenhum_criterio, "Valor Comprado"] = 0

    # =========================
    # Busca histórico de consumo quarto mes completo
    # =========================

    from datetime import datetime


    data = datetime.now() - relativedelta(months=4)
    mes = data.month
    ano = data.year
    arquivo_apont = DATA_DIR / f"apont-{ano}-{mes:02d}.csv"
    if not arquivo_apont.exists():
        arquivo_apont = BASE_DIR / f"apont-{ano}-{mes:02d}.csv"
    if arquivo_apont.exists():
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
    df[numeric_cols] = df[numeric_cols].round(3)

    for col in df.select_dtypes(include=["datetime64[ns]"]):
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    df = df.where(pd.notnull(df), None)

    return df


def geral(dfs):
    df_apoio = sanitizar_dataframe(dfs.get("apoio_compras").copy())
    df_entrega = sanitizar_dataframe(dfs.get("conf").copy())

    col_a = df_entrega.columns[0]  # Item
    col_d = df_entrega.columns[3]  # Empresa
    col_f = df_entrega.columns[5]  # Data
    col_l = df_entrega.columns[11]

    # 1) Mantém apenas D == 11
    df_entrega = df_entrega[df_entrega[col_d].astype(str).str.strip() == "11"]
    df_entrega = df_entrega[
        df_entrega[col_l].notna() & (df_entrega[col_l].astype(str).str.strip() != "")
    ]

    # 2) Converte coluna F para data
    df_entrega[col_f] = pd.to_datetime(
        df_entrega[col_f], errors="coerce"
    )

    # 3) Remove linhas sem data válida
    df_entrega = df_entrega[df_entrega[col_f].notna()].dropna(subset=[col_f])

    # 4) Ordena pelos mais recentes
    df_entrega = df_entrega.sort_values(by=col_f, ascending=False)

    # 5) Mantém somente os 5 mais recentes por item
    df_entrega = df_entrega.groupby(col_a, group_keys=False).head(5)

    # 6) Ordenação final
    df_entrega = df_entrega.sort_values(by=[col_a, col_f], ascending=[True, False])

    df = df_apoio

    # =========================
    # Busca histórico de consumo quarto mes completo
    # =========================

    data = datetime.now() - relativedelta(months=4)
    mes = data.month
    ano = data.year
    arquivo_apont = DATA_DIR / f"apont-{ano}-{mes:02d}.csv"
    if not arquivo_apont.exists():
        arquivo_apont = BASE_DIR / f"apont-{ano}-{mes:02d}.csv"
    if arquivo_apont.exists():
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
    df_apoio = df

    meses_historicos, mes_atual = detectar_meses(df_apoio.columns)
    df = processar_analise_compras(df_apoio, df_entrega)

    # Mapeamento dinâmico dos meses calculados
    mapa_meses = {
        "Cons 1": meses_historicos[0],
        "Cons 2": meses_historicos[1],
        "Cons 3": meses_historicos[2],
        "Cons 4": meses_historicos[3],
        "Cons mês atual": mes_atual,
    }
    df = df.rename(columns=mapa_meses)

    # Normalização e renomeação dos campos para interface e compatibilidade
    mapa_colunas = {
        "Desc": "Descrição",
        "Obs.": "Observação",
        "Neces.": "Neces",
        "OC.": "OC",
        "Estoque prod.": "Estoque Produção",
        "Lote min.": "Lote Mínimo",
        "Lote mult.": "Lote Econom",
        "Prazo cadastrado": "Prazo Fornecedor",
        "Familia": "Família",
        "Saldo virtual": "Saldo Virtual",
        "Valor unitário": "Valor Unitário",
        "Cons diário": "Média Diária",
        "Decisão de compra": "Decis Compras",
        "VALOR-COMPRA": "Valor Comprado",
    }
    df = df.rename(columns=mapa_colunas)

    is_aligned = len(df) == len(df_apoio) and (
        df["Item"].values == df_apoio["Item"].astype(str).str.strip().values
    ).all()

    # Campos derivados complementares
    if "Valor Estoque" not in df.columns:
        if "Estoque Padrão" in df.columns and "Valor Unitário" in df.columns:
            df["Valor Estoque"] = (df["Estoque Padrão"] * df["Valor Unitário"]).round(3)
        elif "Valor Estoque" in df_apoio.columns:
            if is_aligned:
                df["Valor Estoque"] = pd.to_numeric(
                    df_apoio["Valor Estoque"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                    errors="coerce"
                ).fillna(0.0).values
            else:
                serie_val = df_apoio.drop_duplicates(subset=["Item"], keep="last").set_index("Item")["Valor Estoque"]
                df["Valor Estoque"] = pd.to_numeric(
                    df["Item"].map(serie_val).astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
                    errors="coerce"
                ).fillna(0.0)

    feriados = carregar_feriados()
    feriados_pd = pd.to_datetime(feriados)
    feriados_np = np.array(feriados_pd, dtype="datetime64[D]")

    prazo_dias = (
        pd.to_numeric(df["Prazo Fornecedor"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    df["Data OC"] = pd.to_datetime("today").normalize() + pd.to_timedelta(
        prazo_dias, unit="D"
    )
    datas = df["Data OC"].values.astype("datetime64[D]")
    df["Data OC"] = np.busday_offset(
        datas, offsets=0, roll="forward", holidays=feriados_np
    )
    df["Data OC"] = pd.to_datetime(df["Data OC"]).dt.strftime("%d/%m/%Y")

    df["texto OC"] = ""
    df["Falta"] = np.maximum(
        0.0,
        df["Neces"] - (df["Estoque Produção"] + df["Estoque Padrão"] + df["OC"])
    ).round(3)

    for extra_col in [
        "Última Data Entrada",
        "Última Data Saída",
        "Estoque Rejeitado",
        "raiz_Item Final",
        "raiz_Pedido",
    ]:
        if extra_col in df_apoio.columns and extra_col not in df.columns:
            if is_aligned:
                df[extra_col] = df_apoio[extra_col].fillna("").values
            else:
                serie_extra = df_apoio.drop_duplicates(subset=["Item"], keep="last").set_index("Item")[extra_col]
                df[extra_col] = df["Item"].map(serie_extra).fillna("")

    # =========================
    # SELEÇÃO E ORDENAÇÃO DE COLUNAS
    # =========================
    colunas_mes = [*meses_historicos, mes_atual]
    colunas_desejadas = [
        "Item",
        "Descrição",
        *colunas_mes,
        "Decis Compras",
        "Valor Comprado",
        "Analisar",
        "Ponto de pedido",
        "Status",
        "Faixa de compra",
        "Saldo Virtual",
        "Dias de saldo virtual",
        "Cobertura mínima (dias)",
        "Sugestão de compra (dias)",
        "Compra com ajuste (dias)",
        "QTD COMPRA",
        "Média mens + Necessidade",
        "Média Diária",
        "Neces",
        "Estoque Padrão",
        "Estoque Produção",
        "OC",
        "Falta",
        "Lote Mínimo",
        "Lote Econom",
        "Valor Unitário",
        "Valor Estoque",
        "Prazo Fornecedor",
        "Média prazos de entrega (5 - 3 últimos)",
        "Data OC",
        "Dif est-cob",
        "Fator de ajuste",
        "Dias de ajuste",
        "Repres. De cons. Mensal",
        "Baixa",
        "Observação",
        "Última Data Entrada",
        "Última Data Saída",
        "Família",
        "texto OC",
    ]

    df = df[[col for col in colunas_desejadas if col in df.columns]]

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].round(3)

    for col in df.select_dtypes(include=["datetime64[ns]"]):
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    df = df.where(pd.notnull(df), None)

    return df


def calcular(analise, dfs):
    """
    Recebe o dicionário dfs = {"apoio_compras": df}
    e retorna UM ÚNICO DataFrame (para o pipeline gerar o JSON)
    """

    if not dfs or dfs.get("apoio_compras") is None:
        raise ValueError(
            "Dados incompletos ou vazios retornados pela extração (grupo 'apoio_compras' ausente). Verifique as credenciais ou a conexão com o sistema PCP."
        )

    if analise == "compra por necessidade":
        analise_compra = compra_necessidade(dfs)
    elif analise == "ABR - ACE":
        analise_compra = abr_ace(dfs)
    elif analise == "FND - FER":
        analise_compra = fnd_fer(dfs)
    elif analise == "Geral":
        analise_compra = geral(dfs)
    else:
        raise NotImplementedError(f"Análise '{analise}' ainda não implementada")
    return analise_compra


def calcular_com_apoio_30(analise, dfs):
    """
    Executa a orquestração de cálculo desacoplada.
    1. Executa o cálculo base para o horizonte geral.
    2. Fallback: Se a coluna 'Neces (30 dias)' não existir em apoio_compras, retorna o DataFrame base.
    3. Se existir, recalcula no mesmo motor com 'Neces' substituído e faz o merge das colunas '_N30'.
    """
    df_base = calcular(analise, dfs)

    if not dfs or dfs.get("apoio_compras") is None:
        return df_base

    df_apoio = dfs["apoio_compras"]
    col_30 = None
    for cand in ["Neces (30 dias)", "Neces(30 dias)", "Neces 30", "Neces_30"]:
        if cand in df_apoio.columns:
            col_30 = cand
            break

    if col_30 is None:
        return df_base

    try:
        # Clona dicionário de DataFrames e apoio_compras para isolar os cálculos
        dfs_30 = dfs.copy()
        df_apoio_30 = df_apoio.copy()
        df_apoio_30["Neces"] = df_apoio_30[col_30]
        dfs_30["apoio_compras"] = df_apoio_30

        df_30 = calcular(analise, dfs_30)

        colunas_impactadas = [
            "Neces",
            "Decis Compras",
            "Valor Comprado",
            "Saldo Virtual",
            "Falta",
            "Ponto de pedido",
            "Sugestão de compra (dias)",
            "Compra com ajuste (dias)",
            "Cobertura mínima (dias)",
            "Dias de saldo virtual",
            "Média mens + Necessidade",
            "Analisar",
            "Status",
        ]

        is_aligned = len(df_base) == len(df_30) and (
            df_base["Item"].values == df_30["Item"].values
        ).all()

        for col in colunas_impactadas:
            if col in df_30.columns:
                col_n30 = f"{col}_N30"
                if is_aligned:
                    df_base[col_n30] = df_30[col].values
                else:
                    mapa_30 = df_30.drop_duplicates(subset=["Item"], keep="last").set_index("Item")[col]
                    df_base[col_n30] = df_base["Item"].map(mapa_30)

    except Exception as e:
        print(f"Aviso: Não foi possível processar cálculo secundário de 30 dias: {e}")

    return df_base
