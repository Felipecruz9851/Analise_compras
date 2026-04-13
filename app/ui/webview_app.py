import webview
import threading
import pandas as pd
from app.services.pipeline import executar_pipeline
from app import settings


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
        }

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

            return {"status": "ok", "total": len(df)}

    def obter_slice(self, payload):
        if self._df_ativo is None:
            return {"erro": "sem dados"}

        df = self._df_ativo

        start = payload.get("start", 0)
        size = payload.get("size", 50)

        filtros = payload.get("filtros", {})
        ordenacao = payload.get("ordenacao", {})
        correspondencia_exata = payload.get("correspondenciaExata", False)
        filtros_invertidos = payload.get("filtrosInvertidos", False)

        df_filtrado = df

        for col, val in filtros.items():
            if val:
                if correspondencia_exata:
                    mask = df_filtrado[col].astype(str).str.lower() == val.lower()
                else:
                    mask = (
                        df_filtrado[col]
                        .astype(str)
                        .str.lower()
                        .str.contains(val.lower(), na=False)
                    )
                df_filtrado = (
                    df_filtrado[~mask] if filtros_invertidos else df_filtrado[mask]
                )

        if ordenacao.get("coluna"):
            df_filtrado = df_filtrado.sort_values(
                by=ordenacao["coluna"],
                ascending=ordenacao.get("direcao", "asc") == "asc",
            )

        # ✅ define df_calc PRIMEIRO
        df_calc = df_filtrado.copy()

        # ✅ aplica edições antes de tudo
        if self._edicoes:
            for row_id, valor in self._edicoes.items():
                mask = df_calc["__rowId"] == row_id
                if mask.any():
                    df_calc.loc[mask, "Decis Compras"] = valor
                    if "Valor Unitário" in df_calc.columns:
                        df_calc.loc[mask, "Valor Comprado"] = (
                            df_calc.loc[mask, "Valor Unitário"] * valor
                        )

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


def start():
    api = Api()

    window = webview.create_window(
        "Análise de Compras",
        "app/ui/login.html",
        js_api=api,
        maximized=True,
    )

    webview.start(debug=True)
