import webview
import threading
from app.services.pipeline import executar_pipeline
from app import settings


class Api:
    def __init__(self):
        self._lock = threading.Lock()
        self._allowed_methods = {"listar_analises", "rodar_analise", "filtrar_datas"}

    # 🔒 Gatekeeper
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

    # 📋 Métodos expostos (via whitelist)

    def listar_analises(self):
        return settings.ANALISES

    def rodar_analise(self, payload):
        # 🧪 Validação básica
        if not isinstance(payload, dict):
            return {"erro": "payload inválido"}

        required = ["username", "password", "analise"]
        if not all(k in payload for k in required):
            return {"erro": "faltando campos obrigatórios"}

        # 🚫 Evita execução simultânea
        if self._lock.locked():
            return {"erro": "Processo já em execução"}

        with self._lock:
            return executar_pipeline(
                payload["username"],
                payload["password"],
                payload["analise"],
            )

    def filtrar_datas(self, payload):
        print("I'm here")
        pass


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
