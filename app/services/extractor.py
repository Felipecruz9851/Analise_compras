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


def extrair_dados(username, password, analise):
    """
    Executa o pipeline de extração: login + execução de tarefas.

    Args:
        username: usuário para login
        password: senha para login
        analise: tipo de análise (sugestao, ruptura, excesso)

    Returns:
        Lista de dicionários com os dados extraídos
    """
    session = requests.Session()

    # Realiza login
    login(session, username, password)

    # Gera tarefas
    tarefas, _, _ = gerar_tarefas()

    # Executa tarefas em paralelo
    resultados = []
    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        for tarefa in tarefas:
            future = executor.submit(executar_tarefa, session, tarefa)
            futures.append(future)

        for future in as_completed(futures):
            try:
                resultado = future.result()
                if resultado:
                    resultados.extend(resultado)
            except Exception as e:
                print(f"Erro ao executar tarefa: {e}")

    # Retorna os dados extraídos
    return resultados


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


def executar_tarefa(session: requests.Session, tarefa: dict):
    """
    Executa uma tarefa (requisição HTTP).

    Args:
        session: sessão requests autenticada
        tarefa: dicionário com os dados da tarefa

    Returns:
        Lista de dicionários com os dados extraídos
    """
    method = tarefa.get("method", "GET")
    url = tarefa["url"]
    data = tarefa.get("data", {})
    timeout = tarefa.get("timeout", (10, 60))

    start_time = time.time()

    if method == "POST":
        response = session.post(url, data=data, timeout=timeout)
    else:
        response = session.get(url, timeout=timeout)

    response.raise_for_status()
    elapsed = time.time() - start_time

    # Parse da resposta HTML (extrair tabela)
    dados = parse_html_table(response.text)

    print(f"{tarefa['nome']} concluída em {elapsed:.2f}s - {len(dados)} registros")

    return dados


def parse_html_table(html: str) -> list:
    """
    Parseia uma tabela HTML e retorna uma lista de dicionários.

    Args:
        html: conteúdo HTML da página

    Returns:
        Lista de dicionários com os dados da tabela
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")

    if not table:
        return []

    # Encontra os headers
    headers = []
    thead = table.find("thead")
    if thead:
        for th in thead.find_all("th"):
            headers.append(th.get_text(strip=True).lower().replace(" ", "_"))

    # Se não encontrou headers no thead, tenta no primeiro tr
    if not headers:
        first_tr = table.find("tr")
        if first_tr:
            for th in first_tr.find_all(["th", "td"]):
                headers.append(th.get_text(strip=True).lower().replace(" ", "_"))

    # Extrai as linhas
    dados = []
    tbody = table.find("tbody")
    rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

    for row in rows:
        cells = row.find_all(["td", "th"])
        if len(cells) == len(headers):
            row_data = {}
            for header, cell in zip(headers, cells):
                row_data[header] = cell.get_text(strip=True)
            dados.append(row_data)

    # Normaliza os dados para tipos numéricos
    for row in dados:
        for key, value in row.items():
            # Tenta converter para número
            try:
                row[key] = float(value.replace(".", "").replace(",", "."))
            except (ValueError, AttributeError):
                pass

    return dados
