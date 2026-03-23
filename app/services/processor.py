from pydoc import html
from anyio import Path
import pandas as pd
from bs4 import BeautifulSoup
import time
from app.settings import dict_fam
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty
from threading import Lock
from collections import defaultdict
from typing import Dict


def extract_table(html: str) -> pd.DataFrame:
    data_ref = time.strftime("%Y-%m")

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", attrs={"border": "1"})
    if table is None:
        raise ValueError("Tabela de dados não encontrada")

    rows = table.find_all("tr")

    header = [cell.get_text(strip=True) for cell in rows[0].find_all(["td", "th"])]

    data = []
    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        # ignora linhas quebradas
        if len(cols) != len(header):
            continue

        data.append(cols)

    df = pd.DataFrame(data, columns=header)

    # só remove se existir
    if data_ref in df.columns:
        df = df.drop(columns=[data_ref])

    return df


def juntar_tabelas(resultados):
    from collections import defaultdict
    import pandas as pd

    grupos = defaultdict(list)

    for html, familia, grupo in resultados:
        try:
            df = extract_table(html)
            df["Família"] = familia
            grupos[grupo].append(df)
        except Exception as e:
            print(f"Erro ao interpretar tabela: {e}")

    dfs = {}
    for grupo, lista_dfs in grupos.items():
        if len(lista_dfs) > 1:
            dfs[grupo] = pd.concat(lista_dfs, ignore_index=True)
            print(f"Grupo '{grupo}': {len(lista_dfs)} tabelas unidas")
        else:
            dfs[grupo] = lista_dfs[0]
            print(f"Grupo '{grupo}': tabela única")
    #####  Salva em Excel #####
    # for nome, df in dfs.items():
    # 	 try:
    # 		 df.to_excel(f"{nome}.xlsx", index=False)
    # 	 except Exception as e:
    # 		 print(f"[ERRO] {nome} -> {type(e).__name__}: {e}")

    return dfs  # ← dicionário { "ordens": df }


def processar_stream(
    processing_queue: Queue, max_workers: int = 8
) -> Dict[str, pd.DataFrame]:
    """
    Processa itens da queue em paralelo, extraindo tabelas e agrupando.
    Assume queue recebe (html, familia, grupo) até esvaziar.
    """
    grupos = defaultdict(list)
    lock = Lock()

    def worker():
        while True:
            try:
                item = processing_queue.get(timeout=1)
                html, familia, grupo = item
                processing_queue.task_done()

                try:
                    df = extract_table(html)
                    df["Família"] = familia
                    with lock:
                        grupos[grupo].append(df)
                    print(f"Processado {grupo} ({familia or 'N/A'})")
                except Exception as e:
                    print(f"Erro ao interpretar tabela: {e}")
            except Empty:
                break
            except Exception as e:
                print(f"Erro worker: {e}")
                break

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker) for _ in range(max_workers)]
        # Aguardar todos tasks na queue (processamento termina quando fetch acaba)
        processing_queue.join()

    # Juntar grupos
    dfs = {}
    for grupo, lista_dfs in grupos.items():
        if len(lista_dfs) > 1:
            dfs[grupo] = pd.concat(lista_dfs, ignore_index=True)
            print(f"Grupo '{grupo}': {len(lista_dfs)} tabelas unidas")
        else:
            dfs[grupo] = lista_dfs[0]
            print(f"Grupo '{grupo}': tabela única")

    return dfs
