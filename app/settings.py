from pathlib import Path
from datetime import date
import csv
import pandas as pd

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
    "Compra est NEC conf",
]

FAMILIAS = {
    "compra por necessidade": "FNC,VSN,VRG,NEC,IDA",
    # "Compra est NEC conf": "ACE,ARM,CRD,DBR,FEC,GIR,PEZ,PUX,RDZ",
    "Compra est NEC conf": "ABR,ACE,ARM,AVI,COL,CRD,DBR,EMB,EPM,ETI,FOR,GIR,MAN,PEZ,PRF,PUX,RDZ,FER,FIB,FND,VPE,LAM,FEC,GAS,LNH,REV,MIN",
}

LOCAIS = {
    "COLCHOES",
    "BOX",
    "ESTOF UL",
    "CC ACABA01",
    "ARMARIO UL",
    "UL ACABA01",
    "COZINHA",
    "PES ACABA",
    "VIDRACARIA",
    "PORTAS",
    "LAMINAD UL",
    "TAMPOS UL",
    "UL FABRI01",
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
    "PLAN_ESP",
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


# =====================================================================
DIAS_FABRICA = [
    {"local": "CADEIRAS", "tipo": "(N)", "dias": 4},
    {"local": "CC FABRI01", "tipo": "(N)", "dias": 3},
    {"local": "CC FABRI01", "tipo": "(LA)", "dias": 4},
    {"local": "CC FABRI01", "tipo": "ESPECIAL", "dias": 4},
    {"local": "CC FABRI01", "tipo": "", "dias": 3},
    {"local": "ESTOF UL", "tipo": "", "dias": 9},
    {"local": "CENTRO DE ACABAMENTO", "tipo": "", "dias": 7},
    {"local": "ACESSORIOS", "tipo": "", "dias": 7},
]

# =====================================================================
PRAZOS_EXPEDICAO = [
    # valores únicos
    {"tipo": "valores", "itens": [7, 9, 95, 202, 762, 724], "prazo": 3},
    {"tipo": "valores", "itens": [201, 203, 241, 261], "prazo": 3},
    {"tipo": "valores", "itens": [700], "prazo": 3},
    {"tipo": "valores", "itens": [601, 602, 603], "prazo": 10},
    # intervalos
    {"tipo": "intervalo", "de": 50, "ate": 90, "prazo": 3},
    {"tipo": "intervalo", "de": 1000, "ate": 1999, "prazo": 3},
    {"tipo": "intervalo", "de": 2000, "ate": 2999, "prazo": 8},
    {"tipo": "intervalo", "de": 3000, "ate": 3999, "prazo": 8},
    {"tipo": "intervalo", "de": 4000, "ate": 5999, "prazo": 8},
    {"tipo": "intervalo", "de": 6000, "ate": 6999, "prazo": 8},
    {"tipo": "intervalo", "de": 7000, "ate": 7999, "prazo": 8},
    {"tipo": "intervalo", "de": 9000, "ate": 9999, "prazo": 8},
    {"tipo": "intervalo", "de": 300, "ate": 499, "prazo": 10},
    {"tipo": "intervalo", "de": 8000, "ate": 8999, "prazo": 10},
]


def prazo_por_representante(rep: int | str) -> int:
    if pd.isna(rep):
        return 0

    rep = int(rep)

    # # regra especial
    # if str(rep).endswith("95"):
    #     return 3

    # valores específicos primeiro
    for regra in PRAZOS_EXPEDICAO:
        if regra["tipo"] == "valores" and rep in regra["itens"]:
            return regra["prazo"]

    # depois intervalos
    for regra in PRAZOS_EXPEDICAO:
        if regra["tipo"] == "intervalo" and regra["de"] <= rep <= regra["ate"]:
            return regra["prazo"]

    return 10  # fallback consistente


if __name__ == "__main__":

    print("insira um valor de representante para obter o prazo de expedição:")
    rep = int(input())
    prazo = prazo_por_representante(rep)
    print(prazo)
