from app.services.extractor import extrair_dados
from app.services.processor import processar
from app.services.purchase_logic import aplicar_logica

def executar_pipeline(username, password, analise):

    dados = extrair_dados(username, password, analise)
    df = processar(dados)
    df = aplicar_logica(df, analise)

    return df.to_dict(orient="records")