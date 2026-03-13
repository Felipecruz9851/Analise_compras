from pathlib import Path
from datetime import date
import csv

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

ANALISES = [
    "compra por necessidade",
    "Compra para estoque",
    "rev",
    "lam",
    "compra para estoque ignora necess.",
]

FAMILIAS = {
    "compra por necessidade": "FNC,CST,RV,VSN,CSD,VRG,NEC",
}

LOCAIS = {
    "COLCHOES",
    "BOX",
    "ESTOF UL",
    "CC ACABA01",
    "ARMARIO UL",
    "UL ACABA01",
    "COZINHAPES ACABA",
    "VIDRACARIAPORTAS",
    "LAMINAD UL",
    "TAMPOS ULUL FABRI01",
    "CORTE",
    "CADEIRAS",
    "CC FABRI01",
    "CORTE LE",
    "PEZINHO",
    "CC FABRI03",
    "PLANEJADOS",
    "LE FABRI02",
    "LE FABRI03",
    "LE FABRI06",
    "FIBRA",
    "ALMOFADAS",
    "CAPAS LE",
    "METALURGIA",
    "ALUMINIO",
    "INOX",
    "PLASMA",
    "ATELIE",
    "ATELIE2",
    "UL-ALMOX05",
    "REVENDA",
    "AT INSUMO",
    "AT SOFA",
    "AT MOVEIS",
    "AT KIT",
    "AT VIDRO",
    "KIT",
    "TAPA FURO",
    "ACESSORIOS",
    "COLMEIAS",
    "C PILOTO",
    "MOSTRUARIO",
    "LAMINACAO1",
    "EMBALAGEM",
    "OSSOPAINEL",
    "TAPETES",
    "LE FABRI01",
}


def carregar_familias() -> dict:
    caminho_csv = Path(__file__).with_name("familias.csv")
    familias = {}

    with open(caminho_csv, mode="r", encoding="utf-8") as arquivo:
        reader = csv.DictReader(arquivo, delimiter=";")
        print(reader.fieldnames)
        for linha in reader:
            item = linha["Item"].strip()
            familia = (linha.get("Familia") or "").strip()
            familias[item] = familia

    return familias


dict_fam = carregar_familias()


if __name__ == "__main__":

    print(FERIADOS_BRASIL)
