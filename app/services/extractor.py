import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


BASE_URL = "http://192.168.0.6"

LOGIN_PAGE = f"{BASE_URL}/home/"
LOGIN_POST = f"{BASE_URL}/home/login/"

ORDEM_URL = f"{BASE_URL}/pcp/atrasadas.php"

# Valores padrão (podem ser sobrescritos)
USUARIO = "felipe.cruz"
SENHA = "#Gladoscruz.9851"
LOCAL = "ESTOF UL"
DATA_INICIO = "2000-01-01"
DATA_FIM = "2060-12-31"


def login(session: requests.Session, usuario: str, senha: str) -> None:
    """Realiza login na aplicação"""
    session.get(LOGIN_PAGE, timeout=10)

    response = session.post(
        LOGIN_POST,
        files={
            "pagina_acessada": (None, f"{BASE_URL}/home/login/"),
            "action": (None, "login"),
            "usuario": (None, usuario),
            "senha": (None, senha),
            "logar": (None, "Acessar"),
        },
        headers={
            "Referer": LOGIN_PAGE,
            "Origin": BASE_URL,
            "User-Agent": "Mozilla/5.0",
        },
        allow_redirects=True,
        timeout=10,
    )

    response.raise_for_status()

    if "PHPSESSID" not in session.cookies:
        raise RuntimeError("Login falhou: sessão não criada")
        print("Login falhou: sessão não criada")


def gerar_tarefas(
    usuario=None, senha=None, local=None, data_inicio=None, data_fim=None
):
    """
    Gera a lista de tarefas com os parâmetros fornecidos.
    Se não fornecidos, usa os valores padrão (hardcoded).
    """
    _usuario = usuario or USUARIO
    _senha = senha or SENHA
    _local = local or LOCAL
    _data_inicio = data_inicio or DATA_INICIO
    _data_fim = data_fim or DATA_FIM

    tarefas = [
        {
            "nome": "ordem_acessorio",
            "method": "POST",
            "url": ORDEM_URL,
            "data": {
                "cod_empresa": "11",
                "inicio": _data_inicio,
                "fim": _data_fim,
                "local[]": _local,
                "ordem": "entrega,",
            },
            "timeout": (5, 600),
        },
    ]

    return tarefas, _usuario, _senha
