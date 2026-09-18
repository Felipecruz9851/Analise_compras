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
        df_calc.groupby("Família")["Valor Comprado"]
        .sum()
        .sort_values(ascending=False)
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
        df_html.groupby("Família")["Valor Comprado"]
        .sum()
        .sort_values(ascending=False)
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
    files = sorted(
        base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True
    )

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
    
    files = sorted(
        exports_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True
    )

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
    
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for nome in payload["arquivos"]:
            p = exports_dir / nome
            if p.exists() and p.is_file() and p.resolve().parent == exports_dir.resolve():
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
            return {"erro": f"Arquivo '{pkl_path}' não encontrado. Gere os snapshots primeiro usando 'Gerar Dados'."}

        with open(pkl_path, "rb") as f:
            dfs = pickle.load(f)

        apoio_comp = dfs.get("apoio_compras").copy()

        # Histórico de consumo do quarto mês completo
        data_ref = datetime.now() - relativedelta(months=4)
        mes = data_ref.month
        ano = data_ref.year
        arquivo_apont = Path(f"apont-{ano}-{mes:02d}.csv")
        if arquivo_apont.exists():
            df_apont = pd.read_csv(arquivo_apont, sep=";", decimal=",", encoding="utf-8-sig")
            df_apont = sanitizar_dataframe(df_apont)
            df_apont = df_apont[["Item", "Qtde."]].groupby("Item", as_index=False).sum()
            nome_col = f"{ano}-{mes:02d}"
            apoio_comp[nome_col] = apoio_comp["Item"].map(df_apont.set_index("Item")["Qtde."]).fillna(0)
            if nome_col in apoio_comp.columns:
                col = apoio_comp.pop(nome_col)
                apoio_comp.insert(2, nome_col, col)
            else:
                apoio_comp.insert(2, nome_col, pd.NA)
            apoio_comp = apoio_comp.reindex(
                columns=apoio_comp.columns.drop("Baixa").tolist() + ["Baixa"]
            )

        apoio_comp.to_csv("CSV/apoio.csv", index=False, sep=";", decimal=",", encoding="utf-8-sig")

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
        df_conf = df_conf[df_conf[col_l].notna() & (df_conf[col_l].astype(str).str.strip() != "")]
        df_conf[col_f] = pd.to_datetime(df_conf[col_f], errors="coerce", dayfirst=True)
        df_conf = df_conf[df_conf[col_f].notna()].dropna(subset=[col_f])
        df_conf = df_conf.sort_values(by=col_f, ascending=False)
        df_conf = df_conf.groupby(col_a, group_keys=False).head(5)
        df_conf = df_conf.sort_values(by=[col_a, col_f], ascending=[True, False])
        df_conf.to_csv(caminho_conf, index=False, sep=";")

        return {"status": "ok", "mensagem": "CSVs gerados com sucesso a partir dos snapshots."}

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
            resp.append({
                "nome": p.name,
                "url": f"/csv_files/{p.name}",
                "tamanho": f"{st.st_size / 1024:.1f} KB",
                "data_criacao": dt.strftime("%Y-%m-%d %H:%M:%S"),
            })
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
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for nome in payload["arquivos"]:
            p = csv_dir / nome
            if p.exists() and p.is_file() and p.resolve().parent == csv_dir.resolve():
                zipf.write(p, arcname=nome)
    return {"status": "ok", "url": f"/exports/{zip_name}"}

def _gerar_html_historico(session, data, resumo, total_geral):
    colunas = [c for c in data[0].keys() if c not in ["__rowId", "Gráfico"]]
    import re

    colunas_mes = [c for c in colunas if re.match(r"^\d{4}-\d{2}$", c)] or [
        "2024-01"
    ]
    colunas_tabela = [c for c in colunas if c not in colunas_mes]
    colunas_tabela.insert(2, "Gráfico")

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
            if col == "Gráfico":
                html_tbody += "<td>-</td>"
            elif col == "Decis Compras":
                val = row.get(col, "")
                html_tbody += f'<td class="col-destaque-verde">{val}</td>'
            elif col == "Valor Comprado":
                val = row.get(col, 0)
                html_tbody += f'<td class="col-destaque-verde">R$ {val:,.2f}</td>'
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
    
    colunas_html = ''.join([f'<th>{c}</th>' for c in colunas_tabela])
    
    return f"""<!DOCTYPE html>
<html>
<head>
  <title>OCs {analise_nome} {today_str}</title>
  <link rel="stylesheet" href="styles.css">
  <style>
    body {{ font-family: Arial; margin: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
    .col-destaque-verde {{ background-color: #d4edda; font-weight: bold; }}
    .familia-item {{ display: flex; justify-content: space-between; padding: 5px; }}
    .familia-total {{ background-color: #e9ecef; font-weight: bold; }}
  </style>
</head>
<body>
  <h1>Histórico OCs - {analise_nome} - {today_str}</h1>
  <h2>Resumo por Família</h2>
  <div id="resumoFamilias">{html_resumo}</div>
  <h2>Tabela Completa (sem filtros)</h2>
  <table>
    <thead>
      <tr>
{colunas_html}
      </tr>
    </thead>
    <tbody>{html_tbody}</tbody>
  </table>
</body>
</html>"""
