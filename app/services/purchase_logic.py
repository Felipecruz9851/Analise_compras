def aplicar_logica(df, analise):

    if analise == "sugestao":
        df["sugestao_compra"] = (df["consumo_dia"] * 10) - df["estoque"]
        df["sugestao_compra"] = df["sugestao_compra"].clip(lower=0)

    elif analise == "ruptura":
        df["risco"] = df["dias_estoque"] < 5

    elif analise == "excesso":
        df["excesso"] = df["dias_estoque"] > 30

    return df