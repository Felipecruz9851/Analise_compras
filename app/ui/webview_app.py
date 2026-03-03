import webview
import logging
from app.services.pipeline import executar_pipeline
from app import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Api:
    def listar_analises(self):
        logger.debug("listar_analises called")
        return settings.ANALISES

    def rodar_analise(self, payload):
        logger.debug(f"rodar_analise called with: {payload}")
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
    )

    webview.start(debug=False)
