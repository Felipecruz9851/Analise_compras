from app.services.extractor import Extractor
from app.services.processor import extract_table


def executar_pipeline(username, password, analise):

    extractor = Extractor(username, password)

    html_resultados = extractor.executar(analise)
    df = extract_table(html_resultados)
    print(df.head())
    # depois você processa HTML aqui
    # transforma em dataframe
    # aplica lógica de compra

    return df.to_dict(orient="records")
