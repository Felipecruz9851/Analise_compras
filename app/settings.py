from pathlib import Path
from datetime import date


FERIADOS_TXT = Path(__file__).with_name("feriados.txt")


def carregar_feriados(caminho=FERIADOS_TXT):
    feriados = []

    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()

            if not linha or linha.startswith("#"):
                continue

            feriados.append(date.fromisoformat(linha))

    return feriados


FERIADOS_BRASIL = carregar_feriados()

ANALISES = ["Compra para estoque",
            "compra por necessidade",
            "rev",
            "lam"]


if __name__ == "__main__":
  
    print(FERIADOS_BRASIL)