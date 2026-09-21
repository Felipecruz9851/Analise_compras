from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import date
from pathlib import Path
import os
import pickle
from time import perf_counter

from app.services.pipeline import executar_pipeline, coletar_dados
from app import settings
from app.context import session_id_var
from app.session_manager import get_session

router = APIRouter()


class CallPayload(BaseModel):
    payload: Optional[Dict[str, Any]] = None


@router.get("/listar_analises")
def listar_analises():
    return settings.ANALISES


@router.post("/call/{method}")
def call_method(method: str, req: CallPayload):
    session_id = session_id_var.get()
    session = get_session(session_id)

    if method == "rodar_analise":
        return rodar_analise(session, req.payload)
    elif method == "obter_slice":
        return obter_slice(session, req.payload)
    elif method == "salvar_edicao":
        return salvar_edicao(session, req.payload)
    elif method == "gerar_ocs":
        return gerar_ocs(session, req.payload)
    elif method == "abre_pasta":
        return abre_pasta(session, req.payload)
    elif method == "gerar_pickles":
        return gerar_pickles(session, req.payload)
    elif method == "listar_pickles":
        return listar_pickles(session, req.payload)
    elif method == "listar_exports":
        return listar_exports(session, req.payload)
    elif method == "excluir_exports":
        return excluir_exports(session, req.payload)
    elif method == "baixar_zip":
        return baixar_zip(session, req.payload)
    elif method == "executar_carrega_dados":
        return executar_carrega_dados(session, req.payload)
    elif method == "listar_csv":
        return listar_csv(session, req.payload)
    elif method == "excluir_csv":
        return excluir_csv(session, req.payload)
    elif method == "baixar_zip_csv":
        return baixar_zip_csv(session, req.payload)
    else:
        return {"erro": "Método não permitido ou inexistente"}


def rodar_analise(session, payload):
    if session.lock.locked():
        return {"erro": "Processo já em execução"}

    with session.lock:
        resultado = executar_pipeline(
            payload["username"],
            payload["password"],
            payload["analise"],
        )

        df = pd.DataFrame(resultado)

        # garante ID único
        if "__rowId" not in df.columns:
            df["__rowId"] = range(len(df))

        session.df_base = df
        session.df_ativo = df.copy()
        session.analise_nome = payload["analise"]

        return {"status": "ok", "total": len(df)}


def obter_slice(session, payload):
    if session.df_ativo is None:
        return {"erro": "sem dados"}

    df = session.df_ativo

    start = payload.get("start", 0)
    size = payload.get("size", 50)

    filtros = payload.get("filtros", {})
    ordenacao = payload.get("ordenacao", {})
    correspondencia_exata_global = payload.get("correspondenciaExata", False)
    filtros_invertidos_global = payload.get("filtrosInvertidos", False)
    colunas_invertidas = payload.get("colunasInvertidas", {})
    colunas_exatas = payload.get("colunasExatas", {})

    df_trabalho = df.copy()

    if session.edicoes:
        for row_id, valor in session.edicoes.items():
            mask = df_trabalho["__rowId"] == row_id
            if mask.any():
                df_trabalho.loc[mask, "Decis Compras"] = valor
                if "Valor Unitário" in df_trabalho.columns:
                    df_trabalho.loc[mask, "Valor Comprado"] = (
                        df_trabalho.loc[mask, "Valor Unitário"] * valor
                    )

    df_filtrado = df_trabalho

    for col, val in filtros.items():
        if val:
            exata = colunas_exatas.get(col, correspondencia_exata_global)
            if exata:
                if str(val).strip().lstrip("-").replace(".", "", 1).isdigit():
                    try:
                        val_num = float(str(val).replace(",", "."))
                        mask = df_filtrado[col].astype(float) == val_num
                    except:
                        mask = df_filtrado[col].astype(str).str.lower() == val.lower()
                else:
                    mask = df_filtrado[col].astype(str).str.lower() == val.lower()
            else:
                mask = (
                    df_filtrado[col]
                    .astype(str)
                    .str.lower()
                    .str.contains(val.lower(), na=False, regex=False)
                )

            invertido = colunas_invertidas.get(col, filtros_invertidos_global)
            df_filtrado = df_filtrado[~mask] if invertido else df_filtrado[mask]

    if ordenacao.get("coluna"):
        df_filtrado = df_filtrado.sort_values(
            by=ordenacao["coluna"],
            ascending=ordenacao.get("direcao", "asc") == "asc",
        )

    df_calc = df_filtrado.copy()
    total = len(df_calc)

    soma_por_familia = (
        df_calc.groupby("Família")["Valor Comprado"].sum().sort_values(ascending=False)
    )
    resumo = soma_por_familia.to_dict()
    total_geral = soma_por_familia.sum()

    slice_df = df_calc.iloc[start : start + size]

    return {
        "total": total,
        "data": slice_df.to_dict("records"),
        "resumo": resumo,
        "total_geral": float(total_geral),
        "edicoes": session.edicoes,
    }


def salvar_edicao(session, payload):
    row_id = payload.get("rowId")
    valor = payload.get("valor")

    if row_id is None:
        return {"erro": "rowId inválido"}

    if valor is None:
        session.edicoes.pop(row_id, None)
    else:
        session.edicoes[row_id] = valor

    return {"status": "ok"}


def gerar_ocs(session, payload=None):
    if session.df_base is None:
        return {"erro": "Sem dados carregados"}

    from datetime import datetime

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_analise = session.analise_nome or "analise"
    nome_base = f"OCs {nome_analise} - {stamp}"

    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    df_html = session.df_base.copy()

    if session.edicoes:
        for row_id, valor in session.edicoes.items():
            mask = df_html["__rowId"] == row_id
            if mask.any():
                df_html.loc[mask, "Decis Compras"] = valor
                if (
                    "Valor Unitário" in df_html.columns
                    and "Valor Comprado" in df_html.columns
                ):
                    unit = df_html.loc[mask, "Valor Unitário"]
                    df_html.loc[mask, "Valor Comprado"] = unit * float(valor)

    soma_fam = (
        df_html.groupby("Família")["Valor Comprado"].sum().sort_values(ascending=False)
    )
    resumo_html = soma_fam.to_dict()
    total_geral_html = float(soma_fam.sum())

    html_content = _gerar_html_historico(
        session, df_html.to_dict("records"), resumo_html, total_geral_html
    )

    html_path = exports_dir / f"{nome_base}.html"
    html_path.write_text(html_content, encoding="utf-8")

    df_csv = df_html[df_html["Decis Compras"] > 0][
        ["Item", "Data OC", "Decis Compras", "texto OC"]
    ].copy()

    df_csv = df_csv.assign(
        **{
            "texto OC1": "",
            "texto OC2": "",
            "texto OC3": "",
            "texto OC4": "",
        }
    )[
        [
            "Item",
            "Data OC",
            "Decis Compras",
            "texto OC",
            "texto OC1",
            "texto OC2",
            "texto OC3",
            "texto OC4",
        ]
    ]

    csv_path = exports_dir / f"{nome_base}.csv"
    df_csv.to_csv(csv_path, index=False, sep=";", decimal=",")

    return {
        "status": "ok",
        "html": str(html_path.absolute()),
        "csv": str(csv_path.absolute()),
    }


def abre_pasta(session, payload=None):
    exports_dir = Path("exports")
    if not exports_dir.exists():
        return {"erro": "Pasta de exports não existe"}

    path = str(exports_dir.absolute())
    try:
        os.startfile(path)
    except Exception as e:
        pass

    return {"status": "ok", "path": path}


def gerar_pickles(session, payload=None):
    username = payload.get("username") if payload else None
    password = payload.get("password") if payload else None

    if not username or not password:
        return {"erro": "Informe username e password para gerar os pickles"}

    start = perf_counter()
    snapshots = []
    for analise in settings.ANALISES:
        dfs = coletar_dados(username, password, analise)
        fname = f"snapshot_{analise}.pkl"
        if os.path.exists(fname):
            os.remove(fname)

        with open(fname, "wb") as f:
            pickle.dump(dfs, f)
        snapshots.append(fname)

    elapsed = perf_counter() - start
    return {"status": "ok", "gerados": snapshots, "elapsed_sec": elapsed}


def listar_pickles(session, payload=None):
    from datetime import datetime

    base = Path(os.getcwd())
    pattern = "snapshot_*.pkl"
    files = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)

    resp = []
    for p in files:
        st = p.stat()
        dt = datetime.fromtimestamp(st.st_mtime)
        resp.append(
            {
                "nome": p.name,
                "data_criacao": dt.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return resp


def listar_exports(session, payload=None):
    from datetime import datetime

    exports_dir = Path("exports")
    if not exports_dir.exists():
        return []

    files = sorted(exports_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)

    resp = []
    for p in files:
        if p.is_file():
            st = p.stat()
            dt = datetime.fromtimestamp(st.st_mtime)
            resp.append(
                {
                    "nome": p.name,
                    "url": f"/exports/{p.name}",
                    "tamanho": f"{st.st_size / 1024:.1f} KB",
                    "data_criacao": dt.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return resp


def excluir_exports(session, payload=None):
    if not payload or "arquivos" not in payload:
        return {"erro": "Nenhum arquivo informado"}

    exports_dir = Path("exports")
    removidos = []
    for nome in payload["arquivos"]:
        p = exports_dir / nome
        if p.exists() and p.is_file():
            if p.resolve().parent == exports_dir.resolve():
                p.unlink()
                removidos.append(nome)

    return {"status": "ok", "removidos": removidos}


def baixar_zip(session, payload=None):
    if not payload or "arquivos" not in payload:
        return {"erro": "Nenhum arquivo informado"}

    import zipfile
    from datetime import datetime

    exports_dir = Path("exports")
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"Lote_OCs_{stamp}.zip"
    zip_path = exports_dir / zip_name

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for nome in payload["arquivos"]:
            p = exports_dir / nome
            if (
                p.exists()
                and p.is_file()
                and p.resolve().parent == exports_dir.resolve()
            ):
                zipf.write(p, arcname=nome)

    return {"status": "ok", "url": f"/exports/{zip_name}"}


def executar_carrega_dados(session, payload=None):
    """Gera os CSVs a partir dos snapshots .pkl já existentes no servidor."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from pathlib import Path
    import pandas as pd
    import pickle
    from app.services.processor import sanitizar_dataframe

    csv_dir = Path("CSV")
    csv_dir.mkdir(exist_ok=True)

    try:
        analise_apoio = "Compra est NEC conf"
        pkl_path = Path(f"snapshot_{analise_apoio}.pkl")
        if not pkl_path.exists():
            return {
                "erro": f"Arquivo '{pkl_path}' não encontrado. Gere os snapshots primeiro usando 'Gerar Dados'."
            }

        with open(pkl_path, "rb") as f:
            dfs = pickle.load(f)

        apoio_comp = dfs.get("apoio_compras").copy()

        # Histórico de consumo do quarto mês completo
        data_ref = datetime.now() - relativedelta(months=4)
        mes = data_ref.month
        ano = data_ref.year
        arquivo_apont = Path(f"apont-{ano}-{mes:02d}.csv")
        if arquivo_apont.exists():
            df_apont = pd.read_csv(
                arquivo_apont, sep=";", decimal=",", encoding="utf-8-sig"
            )
            df_apont = sanitizar_dataframe(df_apont)
            df_apont = df_apont[["Item", "Qtde."]].groupby("Item", as_index=False).sum()
            nome_col = f"{ano}-{mes:02d}"
            apoio_comp[nome_col] = (
                apoio_comp["Item"].map(df_apont.set_index("Item")["Qtde."]).fillna(0)
            )
            if nome_col in apoio_comp.columns:
                col = apoio_comp.pop(nome_col)
                apoio_comp.insert(2, nome_col, col)
            else:
                apoio_comp.insert(2, nome_col, pd.NA)
            apoio_comp = apoio_comp.reindex(
                columns=apoio_comp.columns.drop("Baixa").tolist() + ["Baixa"]
            )

        apoio_comp.to_csv(
            "CSV/apoio.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig"
        )

        conf = dfs.get("conf").copy()
        conf.to_csv("CSV/conf.csv", index=False, sep=";", encoding="utf-8-sig")

        # Trata conf.csv (mantém apenas D==11, 5 mais recentes por item)
        caminho_conf = Path("CSV/conf.csv")
        df_conf = pd.read_csv(caminho_conf, sep=None, engine="python")
        col_a = df_conf.columns[0]
        col_d = df_conf.columns[3]
        col_f = df_conf.columns[5]
        col_l = df_conf.columns[11]
        df_conf = df_conf[df_conf[col_d].astype(str).str.strip() == "11"]
        df_conf = df_conf[
            df_conf[col_l].notna() & (df_conf[col_l].astype(str).str.strip() != "")
        ]
        df_conf[col_f] = pd.to_datetime(df_conf[col_f], errors="coerce", dayfirst=True)
        df_conf = df_conf[df_conf[col_f].notna()].dropna(subset=[col_f])
        df_conf = df_conf.sort_values(by=col_f, ascending=False)
        df_conf = df_conf.groupby(col_a, group_keys=False).head(5)
        df_conf = df_conf.sort_values(by=[col_a, col_f], ascending=[True, False])
        df_conf.to_csv(caminho_conf, index=False, sep=";")
        #############

        import pickle

        analise = "compra por necessidade"
        # analise = "Compra est NEC conf"
        dfs = {}
        with open(f"snapshot_{analise}.pkl", "rb") as f:
            dfs = pickle.load(f)
        print(f"Snapshot carregado para {analise}.")
        print(dfs.keys())

        # Cálculo com grafos
        import pandas as pd

        print(f"{dfs.keys()}\n")

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
            ordens = ordens.rename(
                columns={"Ordem": "Ordem Prod", "Saldo": "Saldo Prod"}
            )

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

            from tqdm import tqdm

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
                pais_no_cache = [
                    (oc, po, pc) for oc, po, pc in pais if oc in cache_raiz
                ]
                if not pais_no_cache:
                    return None
                if len(pais_no_cache) == 1:
                    return cache_raiz[pais_no_cache[0][0]]
                match = [(oc, po, pc) for oc, po, pc in pais_no_cache if po == pc]
                if len(match) == 1:
                    return cache_raiz[match[0][0]]
                match2 = [
                    (oc, po, pc) for oc, po, pc in pais_no_cache if pc == pedido_filho
                ]
                if match2:
                    return cache_raiz[match2[0][0]]
                return cache_raiz[pais_no_cache[0][0]]

            # BFS top-down
            for nivel in range(1, 12):
                pendentes = consumo[
                    ~consumo["Ordem Cons"].isin(cache_raiz)
                ].drop_duplicates("Ordem Cons")
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
                        x
                        if isinstance(x, dict)
                        else {c: None for c in CAMPOS_RAIZ_COMPLETO}
                    )
                )
            )
            raiz_df = pd.DataFrame(raiz_df.tolist(), index=consumo.index)
            raiz_df.columns = [f"raiz_{c}" for c in CAMPOS_RAIZ_COMPLETO]
            consumo = pd.concat([consumo, raiz_df], axis=1)

            filtro = (consumo["Tipo"] == "C") & (
                consumo["raiz_Entrega Pedido"] < "2027-01-01 00:00:00"
            )
            consumo = consumo[filtro]

            #### Gera Excel ####
            print("gerar excel")
            csv_path = "CSV/"
            consumo.to_excel(csv_path + "consumo.xlsx", index=False)

            print("Concluido")

        calc_data(dfs)

        return {
            "status": "ok",
            "mensagem": "CSVs gerados com sucesso a partir dos snapshots.",
        }

    except Exception as e:
        return {"erro": str(e)}


def listar_csv(session, payload=None):
    from datetime import datetime

    csv_dir = Path("CSV")
    if not csv_dir.exists():
        return []
    files = sorted(csv_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    resp = []
    for p in files:
        if p.is_file():
            st = p.stat()
            dt = datetime.fromtimestamp(st.st_mtime)
            resp.append(
                {
                    "nome": p.name,
                    "url": f"/csv_files/{p.name}",
                    "tamanho": f"{st.st_size / 1024:.1f} KB",
                    "data_criacao": dt.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
    return resp


def excluir_csv(session, payload=None):
    if not payload or "arquivos" not in payload:
        return {"erro": "Nenhum arquivo informado"}
    csv_dir = Path("CSV")
    removidos = []
    for nome in payload["arquivos"]:
        p = csv_dir / nome
        if p.exists() and p.is_file() and p.resolve().parent == csv_dir.resolve():
            p.unlink()
            removidos.append(nome)
    return {"status": "ok", "removidos": removidos}


def baixar_zip_csv(session, payload=None):
    if not payload or "arquivos" not in payload:
        return {"erro": "Nenhum arquivo informado"}
    import zipfile
    from datetime import datetime

    csv_dir = Path("CSV")
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_name = f"CSV_{stamp}.zip"
    zip_path = exports_dir / zip_name
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for nome in payload["arquivos"]:
            p = csv_dir / nome
            if p.exists() and p.is_file() and p.resolve().parent == csv_dir.resolve():
                zipf.write(p, arcname=nome)
    return {"status": "ok", "url": f"/exports/{zip_name}"}


def _gerar_html_historico(session, data, resumo, total_geral):
    colunas = [c for c in data[0].keys() if c not in ["__rowId", "Gráfico"]]
    import re

    colunas_mes = [c for c in colunas if re.match(r"^\d{4}-\d{2}$", c)]
    colunas_tabela = [c for c in colunas if c not in colunas_mes]
    
    # Inserir as colunas de meses no lugar onde ficava o "Gráfico" (posição 2)
    for i, col_mes in enumerate(colunas_mes):
        colunas_tabela.insert(2 + i, col_mes)

    html_resumo = ""
    html_resumo += f"""
    <div class="familia-item familia-total">
      <span class="familia-nome">TOTAL GERAL</span>
      <span class="familia-valor">R$ {total_geral:.2f}</span>
    </div>"""
    for familia, valor in resumo.items():
        pct = (valor / total_geral * 100) if total_geral > 0 else 0
        html_resumo += f"""
    <div class="familia-item">
      <span class="familia-nome">{familia}</span>
      <span class="familia-valor">R$ {valor:.2f}</span>
      <span class="familia-percentual">{pct:.1f}%</span>
    </div>"""

    html_tbody = ""
    for row in data:
        html_tbody += "<tr>"
        for col in colunas_tabela:
            if col == "Decis Compras":
                val = row.get(col, "")
                html_tbody += f'<td class="col-destaque-verde">{val}</td>'
            elif col == "Valor Comprado":
                val = row.get(col, 0)
                try:
                    val_num = float(val)
                except:
                    val_num = 0
                html_tbody += f'<td class="col-destaque-verde">R$ {val_num:,.2f}</td>'
            else:
                val = row.get(col, "")
                html_tbody += (
                    f'<td title="{val}">{str(val)[:100]}...</td>'
                    if len(str(val)) > 100
                    else f"<td>{val}</td>"
                )
        html_tbody += "</tr>"

    today_str = date.today().strftime("%Y-%m-%d")
    analise_nome = session.analise_nome or "analise"

    colunas_html = "".join([f"<th>{c}</th>" for c in colunas_tabela])

    return f"""<!DOCTYPE html>
<html>
<head>
  <title>OCs {analise_nome} {today_str}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: Arial, sans-serif; padding: 16px; background: #f5f5f5; }}
    h1 {{ font-size: 18px; margin-bottom: 8px; color: #2e8b57; }}
    h2 {{ font-size: 14px; margin: 14px 0 6px; color: #555; }}

    /* Resumo por família */
    #resumoFamilias {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 14px;
    }}
    .familia-item {{
      display: flex;
      gap: 8px;
      align-items: center;
      background: white;
      border: 1px solid #ddd;
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 12px;
    }}
    .familia-total {{ background: #d4edda; font-weight: bold; border-color: #2e8b57; }}
    .familia-nome {{ color: #333; }}
    .familia-valor {{ font-weight: bold; color: #2e8b57; }}
    .familia-percentual {{ color: #888; font-size: 11px; }}

    /* Tabela com rolagem */
    .table-wrapper {{
      width: 100%;
      height: calc(100vh - 220px);
      overflow: auto;
      border: 1px solid #ddd;
      border-radius: 8px;
      background: white;
    }}
    table {{
      width: max-content;
      min-width: 100%;
      border-collapse: collapse;
      font-size: 12px;
    }}
    thead th {{
      position: sticky;
      top: 0;
      z-index: 2;
      background: #2e8b57;
      color: white;
      padding: 8px 10px;
      text-align: left;
      white-space: nowrap;
      border-right: 1px solid #27784c;
    }}
    tbody td {{
      padding: 6px 10px;
      border-bottom: 1px solid #eee;
      border-right: 1px solid #f0f0f0;
      white-space: nowrap;
      max-width: 300px;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    tbody tr:hover {{ background: #f0faf4; }}
    .col-destaque-verde {{ background-color: #d4edda; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Histórico OCs — {analise_nome} — {today_str}</h1>
  <h2>Resumo por Família</h2>
  <div id="resumoFamilias">{html_resumo}</div>
  <h2>Tabela Completa</h2>
  
  <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Pesquisar em toda a tabela..." style="width: 100%; padding: 10px; margin-bottom: 10px; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box;">

  <div class="table-wrapper">
    <table id="historicoTable">
      <thead>
        <tr>{colunas_html}</tr>
      </thead>
      <tbody>{html_tbody}</tbody>
    </table>
  </div>

  <script>
    function filterTable() {{
      const filter = document.getElementById("searchInput").value.toUpperCase();
      const trs = document.querySelectorAll("#historicoTable tbody tr");

      for (let i = 0; i < trs.length; i++) {{
        const rowText = trs[i].textContent || trs[i].innerText;
        if (rowText.toUpperCase().indexOf(filter) > -1) {{
          trs[i].style.display = "";
        }} else {{
          trs[i].style.display = "none";
        }}
      }}
    }}
  </script>
</body>
</html>"""
