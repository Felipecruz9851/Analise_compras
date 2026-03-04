from app.services.extractor import Extractor
from app.services.processor import extract_table
from app.services.purchase_logic import calcular


def executar_pipeline(username, password, analise):

    extractor = Extractor(username, password)
    print("Extractor criado com sucesso!")

    html_resultados = extractor.executar(analise)
    print("HTML gerado com sucesso!")

    df = extract_table(html_resultados)
    print("Tabela extraída com sucesso!")
    print(df.head())
    df = calcular(analise, df)
    # depois você processa HTML aqui
    # transforma em dataframe
    # aplica lógica de compra
    df = df.fillna("")

    return df.to_dict(orient="records")
