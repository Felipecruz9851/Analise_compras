import requests
from typing import List, Dict
from pathlib import Path
from datetime import datetime
from queue import Queue
import threading
import json
from time import perf_counter

from app.settings import FAMILIAS, LOCAIS


class Extractor:

    BASE_URL = "http://192.168.0.6"

    LOGIN_PAGE = f"{BASE_URL}/home/"
    LOGIN_POST = f"{BASE_URL}/home/login/"
    APOIO = f"{BASE_URL}/pcp/apoio_compras_pcp_lgx.php"
    ORDENS = f"{BASE_URL}/pcp/atrasadas.php"
    CONS = f"{BASE_URL}/pcp/consumo_alt.php"
    ESTOQUE = f"{BASE_URL}/pcp/estoque_lote.php"

    ARQ_TEMPOS = Path("tempos_execucao.json")

    def __init__(self, username: str, password: str):

        if not username or not password:
            raise ValueError("Usuário e senha são obrigatórios")

        self.username = username
        self.password = password
        self.session = requests.Session()

    # ----------------------------
    # HISTÓRICO DE TEMPOS
    # ----------------------------

    def carregar_tempos(self):

        if not self.ARQ_TEMPOS.exists():
            return {}

        with open(self.ARQ_TEMPOS, "r", encoding="utf-8") as f:
            return json.load(f)

    def salvar_tempos(self, tempos):

        with open(self.ARQ_TEMPOS, "w", encoding="utf-8") as f:
            json.dump(tempos, f, indent=2)

    # ----------------------------
    # LOGIN
    # ----------------------------

    def login(self) -> None:

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

        if "PHPSESSID" not in self.session.cookies:
            raise RuntimeError("Login falhou: sessão não criada")

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
                    "grupo": "apoio_compras",
                }
            )

        for local in LOCAIS:
            tarefas.append(
                {
                    "nome": f"ordens_{local}",
                    "method": "POST",
                    "url": self.ORDENS,
                    "data": {
                        "cod_empresa": "11",
                        "local[]": local,
                        "inicio": "2000-01-01",
                        "fim": "2050-12-31",
                    },
                    "timeout": (5, 600),
                    "grupo": "ordens",
                }
            )

        for local in LOCAIS:
            tarefas.append(
                {
                    "nome": f"cons{local}",
                    "method": "POST",
                    "url": self.CONS,
                    "data": {
                        "cod_empresa": "11",
                        "local[]": local,
                        "dati": "2000-01-01",
                        "datf": "2050-12-31",
                    },
                    "timeout": (5, 600),
                    "grupo": "cons",
                }
            )
        tarefas.append(
            {
                "nome": "estoque",
                "method": "POST",
                "url": self.ESTOQUE,
                "data": {
                    "cod_empresa": "11",
                    "situacao": "L",
                    "relatorio": "R",
                },
                "timeout": (5, 600),
                "grupo": "estoque",
            }
        )

        return tarefas

    # ----------------------------
    # EXECUÇÃO DE TAREFA
    # ----------------------------

    def executar_tarefa(self, tarefa: Dict) -> str:

        response = self.session.request(
            method=tarefa["method"],
            url=tarefa["url"],
            data=tarefa.get("data"),
            timeout=tarefa.get("timeout", 30),
        )

        response.raise_for_status()

        return response.text

    # ----------------------------
    # SALVAR HTML
    # ----------------------------

    def salvar_html(self, conteudo: str, nome_base: str) -> Path:

        pasta = Path("saida_html")
        pasta.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        arquivo = pasta / f"{nome_base}_{timestamp}.html"

        with open(arquivo, "w", encoding="utf-8") as f:
            f.write(conteudo)

        return arquivo

    # ----------------------------
    # WORKER
    # ----------------------------

    def _worker(
        self,
        fila: Queue,
        resultados: list,
        tempos_execucao: dict,
        lock: threading.Lock,
        progresso: dict,
        total: int,
    ):

        extractor = Extractor(self.username, self.password)
        extractor.login()

        while True:

            try:
                tarefa = fila.get_nowait()
            except:
                break

            try:

                inicio = perf_counter()

                html = extractor.executar_tarefa(tarefa)

                duracao = perf_counter() - inicio

                nome = tarefa["nome"]
                familia = tarefa["data"].get("familia")
                grupo = tarefa.get("grupo")

                with lock:

                    resultados.append((html, familia, grupo))

                    # média móvel simples
                    if nome in tempos_execucao:
                        tempos_execucao[nome] = (
                            tempos_execucao[nome] * 0.7 + duracao * 0.3
                        )
                    else:
                        tempos_execucao[nome] = duracao

                    progresso["concluidas"] += 1

                    print(
                        f"{nome} concluída em {duracao:.2f}s "
                        f"({progresso['concluidas']} / {total})"
                    )

            finally:
                fila.task_done()

    # ----------------------------
    # EXECUÇÃO PARALELA
    # ----------------------------

    def executar_paralelo(self, tarefas: List[Dict], max_workers: int = 15):

        fila = Queue()

        for tarefa in tarefas:
            fila.put(tarefa)

        resultados = []
        lock = threading.Lock()

        tempos_execucao = self.carregar_tempos()

        progresso = {"concluidas": 0}
        total = len(tarefas)

        threads = []

        for _ in range(max_workers):

            t = threading.Thread(
                target=self._worker,
                args=(fila, resultados, tempos_execucao, lock, progresso, total),
            )

            t.start()
            threads.append(t)

        fila.join()

        for t in threads:
            t.join()

        self.salvar_tempos(tempos_execucao)

        return resultados

    # ----------------------------
    # PIPELINE COMPLETO
    # ----------------------------

    def executar(self, analise: str):

        tarefas = self.gerar_tarefas(analise)

        tempos = self.carregar_tempos()

        # ordenar tarefas pelas mais lentas primeiro
        tarefas.sort(key=lambda t: tempos.get(t["nome"], 0), reverse=True)

        resultados = self.executar_paralelo(tarefas)

        for html, familia, grupo in resultados:

            if familia:
                nome = f"apoio_compras_{familia}"
            else:
                nome = grupo

            # self.salvar_html(html, nome)

        return resultados
