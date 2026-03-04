import webview
from app.services.pipeline import executar_pipeline
from app import settings


class Api:
    def listar_analises(self):
        return settings.ANALISES

    def rodar_analise(self, payload):
        return executar_pipeline(
            payload["username"], payload["password"], payload["analise"]
        )


def start():
    api = Api()

    window = webview.create_window(
        "Análise de Compras",
        "app/ui/login.html",
        js_api=api,
        maximized=True,
        resizable=True,
    )

    webview.start(debug=True)
