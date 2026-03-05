import requests
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from app.settings import FAMILIAS
from concurrent.futures import ThreadPoolExecutor, as_completed


class Extractor:

    BASE_URL = "http://192.168.0.6"

    LOGIN_PAGE = f"{BASE_URL}/home/"
    LOGIN_POST = f"{BASE_URL}/home/login/"
    APOIO = f"{BASE_URL}/pcp/apoio_compras_pcp_lgx.php"

    def __init__(self, username: str, password: str):
        if not username or not password:
            raise ValueError("Usuário e senha são obrigatórios")

        self.username = username
        self.password = password
        self.session = requests.Session()

    # ----------------------------
    # LOGIN
    # ----------------------------

    def login(self) -> None:
        """
        Realiza login na aplicação e valida autenticação.
        """

        # Primeiro acessa a página inicial para capturar cookies iniciais
        self.session.get(self.LOGIN_PAGE, timeout=10)

        response = self.session.post(
            self.LOGIN_POST,
            data={
                "pagina_acessada": f"{self.BASE_URL}/home/login/",
                "action": "login",
                "usuario": self.username,
                "senha": self.password,
                "logar": "Acessar",
            },
            headers={
                "Referer": self.LOGIN_PAGE,
                "Origin": self.BASE_URL,
                "User-Agent": "Mozilla/5.0",
            },
            allow_redirects=True,
            timeout=10,
        )

        response.raise_for_status()

        # Verifica se sessão foi criada
        if "PHPSESSID" not in self.session.cookies:
            raise RuntimeError("Login falhou: sessão não criada")

        # Verifica se ainda está na página de login
        if "login" in response.url.lower():
            raise RuntimeError("Login falhou: credenciais inválidas")

    # ----------------------------
    # GERAÇÃO DE TAREFAS
    # ----------------------------

    def gerar_tarefas(self, analise: str) -> List[Dict]:

        if analise not in FAMILIAS:
            raise ValueError(f"Análise não suportada: {analise}")

        familias = FAMILIAS[analise].split(",")

        tarefas = []

        for familia in familias:
            tarefas.append(
                {
                    "nome": f"apoio_compras_{familia}",
                    "method": "POST",
                    "url": self.APOIO,
                    "data": {
                        "cod_empresa": "11",
                        "familia": familia,
                        "grupo": "",
                        "local": "",
                        "ordem": "cod_item",
                        "neces_aberto": "S",
                    },
                    "timeout": (5, 600),
                }
            )

        return tarefas

    # ----------------------------
    # EXECUÇÃO DE TAREFA
    # ----------------------------

    def executar_tarefa(self, tarefa: Dict) -> str:
        """
        Executa uma tarefa de scraping.
        """

        response = self.session.request(
            method=tarefa["method"],
            url=tarefa["url"],
            data=tarefa.get("data"),
            timeout=tarefa.get("timeout", 30),
        )

        response.raise_for_status()
        return response.text

    def salvar_html(self, conteudo: str, nome_base: str) -> Path:
        """
        Salva HTML em arquivo organizado por data.
        """

        pasta = Path("saida_html")
        pasta.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        arquivo = pasta / f"{nome_base}_{timestamp}.html"

        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)

        return arquivo

    def worker(self, tarefa: Dict):

        extractor = Extractor(self.username, self.password)
        extractor.login()

        html = extractor.executar_tarefa(tarefa)

        familia = tarefa["data"]["familia"]

        return html, familia

    def executar_paralelo(self, tarefas):

        resultados = []

        with ThreadPoolExecutor(max_workers=len(tarefas)) as executor:

            futures = [executor.submit(self.worker, tarefa) for tarefa in tarefas]

            for future in as_completed(futures):
                resultados.append(future.result())

        return resultados

    # ----------------------------
    # PIPELINE COMPLETO
    # ----------------------------

    def executar(self, analise: str):

        tarefas = self.gerar_tarefas(analise)

        resultados = self.executar_paralelo(tarefas)

        for tarefa, (html, familia) in zip(tarefas, resultados):
            self.salvar_html(html, tarefa["nome"])

        return resultados
