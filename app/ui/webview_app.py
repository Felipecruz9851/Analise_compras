import webview
import threading
import pandas as pd
from app.services.pipeline import executar_pipeline
from app import settings
from datetime import date


class Api:
    def __init__(self):
        self._lock = threading.Lock()
        self._df_base = None
        self._df_ativo = None
        self._edicoes = {}

        self._allowed_methods = {
            "listar_analises",
            "rodar_analise",
            "obter_slice",
            "salvar_edicao",
            "gerar_ocs",
        }
        self._analise_nome = None

    def call(self, method, payload=None):
        if method not in self._allowed_methods:
            return {"erro": "Método não permitido"}

        func = getattr(self, method, None)

        if not func:
            return {"erro": "Método inexistente"}

        try:
            return func(payload) if payload is not None else func()
        except Exception as e:
            return {"erro": str(e)}

    def listar_analises(self):
        return settings.ANALISES

    def rodar_analise(self, payload):
        if self._lock.locked():
            return {"erro": "Processo já em execução"}

        with self._lock:
            resultado = executar_pipeline(
                payload["username"],
                payload["password"],
                payload["analise"],
            )

            df = pd.DataFrame(resultado)

            # garante ID único
            if "__rowId" not in df.columns:
                df["__rowId"] = range(len(df))

            self._df_base = df
            self._df_ativo = df.copy()
            self._analise_nome = payload["analise"]

            return {"status": "ok", "total": len(df)}

    def obter_slice(self, payload):
        if self._df_ativo is None:
            return {"erro": "sem dados"}

        df = self._df_ativo

        start = payload.get("start", 0)
        size = payload.get("size", 50)

        filtros = payload.get("filtros", {})
        ordenacao = payload.get("ordenacao", {})
        correspondencia_exata_global = payload.get("correspondenciaExata", False)
        filtros_invertidos_global = payload.get("filtrosInvertidos", False)
        colunas_invertidas = payload.get("colunasInvertidas", {})
        colunas_exatas = payload.get("colunasExatas", {})

        df_trabalho = df.copy()

        # ✅ APLICA EDIÇÕES PRIMEIRO, ANTES DE FILTRAR
        if self._edicoes:
            for row_id, valor in self._edicoes.items():
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
                # Verifica se essa coluna tem correspondencia exata ativada individualmente
                exata = colunas_exatas.get(col, correspondencia_exata_global)

                if exata:
                    # Verifica se valor é numérico para comparar como numero e não string
                    if str(val).strip().lstrip("-").replace(".", "", 1).isdigit():
                        # Comparacao numerica exata para evitar 10 == 100
                        try:
                            val_num = float(str(val).replace(",", "."))
                            mask = df_filtrado[col].astype(float) == val_num
                        except:
                            # Se falhar conversao usa string
                            mask = (
                                df_filtrado[col].astype(str).str.lower() == val.lower()
                            )
                    else:
                        mask = df_filtrado[col].astype(str).str.lower() == val.lower()
                else:
                    mask = (
                        df_filtrado[col]
                        .astype(str)
                        .str.lower()
                        .str.contains(val.lower(), na=False)
                    )

                # Verifica se essa coluna esta invertida individualmente
                invertido = colunas_invertidas.get(col, filtros_invertidos_global)

                df_filtrado = df_filtrado[~mask] if invertido else df_filtrado[mask]

        if ordenacao.get("coluna"):
            df_filtrado = df_filtrado.sort_values(
                by=ordenacao["coluna"],
                ascending=ordenacao.get("direcao", "asc") == "asc",
            )

        # ✅ df_calc já tem as edições aplicadas
        df_calc = df_filtrado.copy()

        total = len(df_calc)

        # ✅ resumo sobre df_calc (já com edições aplicadas)
        soma_por_familia = (
            df_calc.groupby("Família")["Valor Comprado"]
            .sum()
            .sort_values(ascending=False)
        )
        resumo = soma_por_familia.to_dict()
        total_geral = soma_por_familia.sum()

        # ✅ slice_df definido uma única vez
        slice_df = df_calc.iloc[start : start + size]

        return {
            "total": total,
            "data": slice_df.to_dict("records"),
            "resumo": resumo,
            "total_geral": float(total_geral),
            "edicoes": self._edicoes,
        }

    def salvar_edicao(self, payload):
        row_id = payload.get("rowId")
        valor = payload.get("valor")

        if row_id is None:
            return {"erro": "rowId inválido"}

        # remove edição (reset)
        if valor is None:
            self._edicoes.pop(row_id, None)
        else:
            self._edicoes[row_id] = valor

        return {"status": "ok"}

    def gerar_ocs(self, payload=None):
        if self._df_base is None:
            return {"erro": "Sem dados carregados"}

        from datetime import date
        from pathlib import Path
        import os

        today = date.today().strftime("%Y-%m-%d")
        nome_analise = self._analise_nome or "analise"
        nome_base = f"OCs {nome_analise} no payload {today}"

        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)

        # HTML completo sem filtros/edit - dados brutos do df_base
        df_html = self._df_base.copy()

        # Resumo familias
        soma_fam = (
            df_html.groupby("Família")["Valor Comprado"]
            .sum()
            .sort_values(ascending=False)
        )
        resumo_html = soma_fam.to_dict()
        total_geral_html = float(soma_fam.sum())

        # Gerar HTML estático
        html_content = self._gerar_html_historico(
            df_html.to_dict("records"), resumo_html, total_geral_html
        )

        html_path = exports_dir / f"{nome_base}.html"
        html_path.write_text(html_content, encoding="utf-8")

        # CSV itens decis >0
        df_csv = df_html[df_html["Decis Compras"] > 0][
            ["Item", "Data OC", "Decis Compras", "texto OC"]
        ].copy()
        csv_path = exports_dir / f"{nome_base}.csv"
        df_csv.to_csv(csv_path, index=False, sep=";", decimal=",")

        return {
            "status": "ok",
            "html": str(html_path.absolute()),
            "csv": str(csv_path.absolute()),
        }

    def _gerar_html_historico(self, data, resumo, total_geral):
        colunas = [c for c in data[0].keys() if c not in ["__rowId", "Gráfico"]]
        import re

        colunas_mes = [c for c in colunas if re.match(r"^\d{{4}}-\d{{2}}$", c)] or [
            "2024-01"
        ]  # fallback
        colunas_tabela = [c for c in colunas if c not in colunas_mes]
        colunas_tabela.insert(2, "Gráfico")  # placeholder

        html_resumo = ""
        html_resumo += """
        <div class="familia-item familia-total">
          <span class="familia-nome">TOTAL GERAL</span>
          <span class="familia-valor">R$ {:.2f}</span>
        </div>""".format(total_geral)
        for familia, valor in resumo.items():
            pct = (valor / total_geral * 100) if total_geral > 0 else 0
            html_resumo += """
        <div class="familia-item">
          <span class="familia-nome">{}</span>
          <span class="familia-valor">R$ {:.2f}</span>
          <span class="familia-percentual">{:.1f}%</span>
        </div>""".format(familia, valor, pct)

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
                        f'<td title="{val}">{val[:100]}...</td>'
                        if len(str(val)) > 100
                        else f"<td>{val}</td>"
                    )
            html_tbody += "</tr>"

        today_str = date.today().strftime("%Y-%m-%d")
        return f"""<!DOCTYPE html>
<html>
<head>
  <title>OCs {self._analise_nome or "analise"} {today_str}</title>
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
  <h1>Histórico OCs - {self._analise_nome or "analise"} - {today_str}</h1>
  <h2>Resumo por Família</h2>
  <div id="resumoFamilias">{html_resumo}</div>
  <h2>Tabela Completa (sem filtros)</h2>
  <table>
    <thead>
      <tr>
{''.join([f'<th>{c}</th>' for c in colunas_tabela])}
      </tr>
    </thead>
    <tbody>{html_tbody}</tbody>
  </table>
</body>
</html>"""


def start():
    api = Api()

    window = webview.create_window(
        "Análise de Compras",
        "app/ui/login.html",
        js_api=api,
        maximized=True,
    )

    webview.start(debug=False)
