import pandas as pd
import numpy as np
import math
import json
import os
import re

# ── Valores padrão (replicam a tabela Capa do Excel) ──────────────────────────
_CONFIG_PADRAO = {
    "faixas_compra": {
        "A": {"dias_cobertura": 7, "recebimentos_max": 3, "ciclo_compra": 0},
        "B": {"dias_cobertura": 20, "recebimentos_max": 3, "ciclo_compra": 0},
        "C": {"dias_cobertura": 60, "recebimentos_max": 3, "ciclo_compra": 0},
    },
    "teto_compra": 2000,
    "estoque_seguranca_dias": 5,
}


def carregar_config(caminho: str = None) -> dict:
    """
    Carrega parâmetros de configuração.

    Prioridade:
      1. Caminho explícito (se fornecido)
      2. config_parametros.json no mesmo diretório deste script
      3. Valores padrão (_CONFIG_PADRAO)
    """
    if caminho is None:
        try:
            # Executa quando o código roda como um script normal (via terminal/Task)
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            # Executa quando o código roda no REPL (Shift + Enter no Zed)
            base_dir = os.getcwd()

        caminho = os.path.join(base_dir, "config_parametros.json")

    if os.path.isfile(caminho):
        with open(caminho, encoding="utf-8") as f:
            return json.load(f)

    return _CONFIG_PADRAO.copy()



# Padrão aceito para o título das colunas de mês: AAAA-MM (ex.: 2026-08)
_PADRAO_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def detectar_meses(colunas) -> tuple:
    """
    Detecta dinamicamente as colunas de mês do DataFrame de entrada.

    Aceita qualquer título no padrão AAAA-MM (ex.: 2026-04, 2025-11), ordena
    cronologicamente e separa:
      - os 4 meses imediatamente anteriores ao mais recente → histórico (Cons 1..4)
      - o mês mais recente                                  → mês atual (Cons mês atual)

    Colunas de mês excedentes (anteriores às 5 mais recentes) são ignoradas,
    pois o cálculo é baseado em 4 meses de histórico + mês corrente.

    Levanta ValueError se forem encontradas menos de 5 colunas de mês.

    Retorna:
        (meses_historicos, mes_atual) → ex.: (['2026-04', ..., '2026-07'], '2026-08')
    """
    meses = sorted(str(c).strip() for c in colunas if _PADRAO_MES.fullmatch(str(c).strip()))

    if len(meses) < 5:
        encontrados = ", ".join(meses) if meses else "nenhuma"
        raise ValueError(
            "Colunas de mês insuficientes: são esperadas pelo menos 5 colunas "
            "no padrão AAAA-MM (4 de histórico + 1 mês atual, ex.: 2026-04 a 2026-08). "
            f"Colunas de mês encontradas: {encontrados}."
        )

    return meses[-5:-1], meses[-1]


def processar_analise_compras(
    df_apoio: pd.DataFrame,
    df_entrega: pd.DataFrame,
    config: dict = None,
) -> pd.DataFrame:
    """
    Processa os cálculos de análise de compras com base em 2 DataFrames.

    Este módulo é projetado para ser acoplado em outra ferramenta.
    Para testes independentes, use o script exemplo_uso.py com arquivos CSV.

    Parâmetros:
    - df_apoio   : dados de apoio de compras. Colunas esperadas:
                   Item, Descrição, colunas de mês no padrão AAAA-MM (detectadas
                   dinamicamente: as 4 mais recentes anteriores viram Cons 1..4 e a
                   mais recente vira Cons mês atual; são necessárias ≥ 5), Estoque
                   Padrão, Estoque Produção, OC, Neces, Prazo Fornecedor,
                   Valor Unitário, Lote Mínimo, Lote Econom, Baixa, Observação, Família.
    - df_entrega : histórico de entregas. Colunas esperadas:
                   Item, Data Entrada, Prazo, Prazo Fornecedor Cad.
    - config     : dicionário de configuração (opcional). Se não fornecido,
                   carrega de config_parametros.json ou usa valores padrão.
                   Chaves: faixas_compra, teto_compra, estoque_seguranca_dias.

    Retorna um DataFrame com as colunas calculadas da análise de compras.
    """
    # Carregar configuração
    if config is None:
        config = carregar_config()
    # 1. Normalização de nomes de colunas do df_apoio
    df_apoio = df_apoio.copy()
    df_apoio.reset_index(drop=True, inplace=True)
    df_apoio.columns = [str(c).replace('\ufeff', '').strip() for c in df_apoio.columns]

    # 1.1 Detecção dinâmica das colunas de mês (título no padrão AAAA-MM)
    meses_historicos, mes_atual = detectar_meses(df_apoio.columns)

    # Tratamento para garantir suporte ao formato brasileiro (caso venha em string com vírgula)
    num_cols_apoio = [
        *meses_historicos, mes_atual,
        'Estoque Padrão', 'Estoque Produção', 'OC', 'Neces',
        'Prazo Fornecedor', 'Valor Unitário', 'Lote Mínimo', 'Lote Econom'
    ]
    for c in num_cols_apoio:
        if c in df_apoio.columns:
            if df_apoio[c].dtype == object:
                df_apoio[c] = df_apoio[c].astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
            df_apoio[c] = pd.to_numeric(df_apoio[c], errors='coerce').fillna(0.0)

    # 2. Processamento do histórico de entregas → média de prazo por item
    # Calcula a partir das 5 entregas mais recentes de cada item.
    df_entrega_clean = df_entrega.copy()
    df_entrega_clean.columns = [str(c).strip() for c in df_entrega_clean.columns]
    df_entrega_clean['Item'] = df_entrega_clean['Item'].astype(str).str.strip()

    if 'Data Entrada' in df_entrega_clean.columns and 'Prazo' in df_entrega_clean.columns:
        df_entrega_clean['Data Entrada'] = pd.to_datetime(df_entrega_clean['Data Entrada'], errors='coerce')
        df_entrega_sorted = df_entrega_clean.sort_values(
            by=['Item', 'Data Entrada'], ascending=[True, False]
        )
        top5 = df_entrega_sorted.groupby('Item').head(5)
        media_entregas = top5.groupby('Item').agg(
            Media_Prazo=('Prazo', 'mean'),
            Count_Entregas=('Prazo', 'count')
        ).reset_index()
    else:
        media_entregas = pd.DataFrame(columns=['Item', 'Media_Prazo', 'Count_Entregas'])

    # 3. Parâmetros de Faixa de Compra (do config / tabela Capa)
    cfg_faixas = config.get('faixas_compra', _CONFIG_PADRAO['faixas_compra'])
    capa_faixas = {}
    for fx_key, fx_val in cfg_faixas.items():
        capa_faixas[fx_key] = {
            'Dias_cob': fx_val['dias_cobertura'],
            'Rec_max': fx_val['recebimentos_max'],
            'Ciclo_compra': fx_val['ciclo_compra'],
        }

    teto_compra = config.get('teto_compra', _CONFIG_PADRAO['teto_compra'])
    est_seg_dias = config.get('estoque_seguranca_dias', _CONFIG_PADRAO['estoque_seguranca_dias'])

    # 4. Construção do DataFrame Resultante
    res = pd.DataFrame()

    # Identificação
    res['Item'] = df_apoio['Item'].astype(str).str.strip()
    res['Desc'] = df_apoio['Descrição'].fillna('').astype(str)
    res['Obs.'] = df_apoio['Observação'].fillna('-').astype(str)

    # Consumo Histórico (colunas de mês detectadas dinamicamente no padrão AAAA-MM)
    for i, col_mes in enumerate(meses_historicos, start=1):
        res[f'Cons {i}'] = df_apoio[col_mes]

    res['Neces.'] = df_apoio['Neces'] if 'Neces' in df_apoio.columns else 0.0
    res['Baixa'] = df_apoio['Baixa'].fillna('').astype(str)
    res['Cons mês atual'] = df_apoio[mes_atual]

    # Consumo Diário
    avg_cons4 = res[['Cons 1', 'Cons 2', 'Cons 3', 'Cons 4']].mean(axis=1)
    cons_d_default = avg_cons4 / 30.0
    sum_h_j = res['Neces.'] + res['Cons mês atual']
    res['Cons diário'] = np.where(cons_d_default == 0, sum_h_j / 60.0, cons_d_default)

    # Estoque & Lotes
    res['OC.'] = df_apoio['OC'] if 'OC' in df_apoio.columns else 0.0
    res['Estoque prod.'] = df_apoio['Estoque Produção'] if 'Estoque Produção' in df_apoio.columns else 0.0
    res['Estoque Padrão'] = df_apoio['Estoque Padrão'] if 'Estoque Padrão' in df_apoio.columns else 0.0

    lmin = df_apoio['Lote Mínimo'] if 'Lote Mínimo' in df_apoio.columns else 1.0
    res['Lote min.'] = np.where(lmin == 0, 1.0, lmin)
    lmult = df_apoio['Lote Econom'] if 'Lote Econom' in df_apoio.columns else 1.0
    res['Lote mult.'] = np.where(lmult == 0, 1.0, lmult)

    res['Prazo cadastrado'] = df_apoio['Prazo Fornecedor'] if 'Prazo Fornecedor' in df_apoio.columns else 0.0

    # Integração Média de Entregas
    res = res.merge(media_entregas, on='Item', how='left')
    res['Média prazos de entrega (5 - 3 últimos)'] = np.where(
        res['Count_Entregas'].fillna(0) < 3,
        res['Prazo cadastrado'],
        res['Media_Prazo'].fillna(res['Prazo cadastrado'])
    )
    res.drop(columns=['Media_Prazo', 'Count_Entregas'], errors='ignore', inplace=True)

    # Colunas1 & Família
    res['Colunas1'] = res['OC.'] + res['Estoque prod.'] + res['Estoque Padrão'] - res['Neces.']
    res['Familia'] = df_apoio['Família'].fillna('').astype(str) if 'Família' in df_apoio.columns else ''

    # Saldo Virtual
    zeros_cons = (res[['Cons 1', 'Cons 2', 'Cons 3', 'Cons 4']] == 0).sum(axis=1)
    cond_rev = (zeros_cons <= 3) & (res['Neces.'] >= 0) & (res['Familia'] == "REV") & (res['Colunas1'] <= 30)

    baixa = df_apoio['Baixa'].fillna('').astype(str).str.strip().str.upper()
    saldo_calc = np.where(cond_rev, res['Colunas1'] - 50.0, res['Colunas1'])
    res['Saldo virtual'] = np.where(baixa == "N", res['Estoque Padrão'] + res['OC.'], saldo_calc)

    res['Colunas2'] = res['Colunas1'] == res['Saldo virtual']

    # Dias de saldo virtual
    res['Dias de saldo virtual'] = np.where(res['Cons diário'] == 0, "-", res['Saldo virtual'] / res['Cons diário'])

    # Média mens + Necessidade
    # Excel: IF(Baixa="S", AVERAGEIF(Cons1:Neces,"<>0"), AVERAGEIF(Cons1:Cons4,"<>0")), IFERROR → 0
    # Neces. só entra na média quando Baixa == "S".
    cons_neces_matrix = res[['Cons 1', 'Cons 2', 'Cons 3', 'Cons 4', 'Neces.']].values
    media_mens_list = []
    for row, bx in zip(cons_neces_matrix, baixa):
        vals = row if bx == "S" else row[:4]
        nz = [v for v in vals if v != 0]
        media_mens_list.append(np.mean(nz) if len(nz) > 0 else 0.0)
    res['Média mens + Necessidade'] = media_mens_list

    # Analisar e Status
    analisar_list = []
    status_list = []
    for idx, r in res.iterrows():
        desc = str(r['Desc']).strip()
        starts_special = desc.startswith('#') or desc.startswith('$') or desc.startswith('~*')
        starts_hash = desc.startswith('#')
        saldo = float(r['Saldo virtual'])
        neces = float(r['Neces.'])
        media_neces = float(r['Média mens + Necessidade'])

        # Cons 1 a Neces (5 colunas)
        cons_neces_vals = [r['Cons 1'], r['Cons 2'], r['Cons 3'], r['Cons 4'], neces]

        # Lógica Analisar
        # Excel: IF(Saldo virtual <= Média mens + Necessidade, "ANALIZAR", ...)
        # A comparação com a média vem antes do teste de divisão por zero,
        # logo Saldo=0 e Média=0 resulta em "ANALIZAR" (e não "ANALIZAR#").
        if saldo <= media_neces:
            analisar = "ANALIZAR"
        elif starts_special:
            analisar = "ANALIZAR"
        else:
            if media_neces == 0:
                # Divisão por zero → IFERROR do Excel
                analisar = "ANALIZAR#"
            else:
                max_val = max(cons_neces_vals)
                # SMALL(range, COUNTIF(range, 0) + 1) -> Menor valor não nulo
                non_zeros = [v for v in cons_neces_vals if v != 0]
                min_non_zero = min(non_zeros) if non_zeros else 0

                diff1 = abs(max_val - media_neces)
                diff2 = abs(min_non_zero - media_neces)
                if max(diff1, diff2) / media_neces > 0.7:
                    analisar = "ANALIZAR"
                else:
                    analisar = "-"
        analisar_list.append(analisar)

        # Lógica Status
        zeros_c14 = sum(1 for v in [r['Cons 1'], r['Cons 2'], r['Cons 3'], r['Cons 4']] if v == 0)

        if starts_hash and saldo >= 0:
            status = "Z"
        elif starts_special:
            status = "Y@"
        elif zeros_c14 == 0:
            status = "X"
        elif zeros_c14 == 4 and neces == 0 and saldo > 0:
            status = "Z"
        else:
            status = "Y"
        status_list.append(status)

    res['Analisar'] = analisar_list
    res['Status'] = status_list

    # Indice de consumo
    ind_cons_list = []
    for idx, r in res.iterrows():
        st = r['Status']
        if st in ['Y', 'Z']:
            ind_cons_list.append(0.0)
        else:
            c1, c2, c3, c4 = r['Cons 1'], r['Cons 2'], r['Cons 3'], r['Cons 4']
            c_arr = [c1, c2, c3, c4]
            avg_c = np.mean(c_arr)
            if avg_c == 0:
                ind_cons_list.append(0.0)
            else:
                val = ((c4 - c1) / avg_c) * (1.0 + (max(c_arr) - min(c_arr)) / avg_c)
                ind_cons_list.append(val)
    res['Indice de consumo'] = ind_cons_list

    # Ajuste cons
    aj_cons_list = []
    for ic in res['Indice de consumo']:
        if ic < -1: aj_cons_list.append(-0.3)
        elif ic < -0.2: aj_cons_list.append(-0.1)
        elif ic <= 0.2: aj_cons_list.append(0.0)
        elif ic <= 1.3: aj_cons_list.append(0.2)
        else: aj_cons_list.append(0.3)
    res['Ajuste cons'] = aj_cons_list

    # Indice futuro
    ind_fut_list = []
    for idx, r in res.iterrows():
        avg_c = avg_cons4.iloc[idx]
        nec = r['Neces.']
        if 1 + avg_c == 0:
            ind_fut_list.append(1.0)
        else:
            ind_fut_list.append((1.0 + nec) / (1.0 + avg_c))
    res['Indice futuro'] = ind_fut_list

    # Ajuste futuro (com arredondamento de precisão flutuante para compatibilidade com o Excel)
    aj_fut_list = []
    for ifut in res['Indice futuro']:
        val = round(ifut, 6)
        if 0.8 <= val <= 1.2: aj_fut_list.append(0.0)
        elif val > 1.2: aj_fut_list.append(0.2)
        elif val < 0.8: aj_fut_list.append(-0.2)
        else: aj_fut_list.append(0.0)
    res['Ajuste futuro'] = aj_fut_list

    # Indice de entrega
    ind_ent_list = []
    for idx, r in res.iterrows():
        m_ent = r['Média prazos de entrega (5 - 3 últimos)']
        p_cad = r['Prazo cadastrado']
        if p_cad == 0:
            ind_ent_list.append(0.0)
        else:
            ind_ent_list.append(m_ent / p_cad)
    res['Indice de entrega'] = ind_ent_list

    # Ajuste de entrega
    res['Ajuste de entrega'] = res['Indice de entrega'] - 1.0

    # Fator de ajuste
    res['Fator de ajuste'] = res['Ajuste cons'] + res['Ajuste futuro'] + res['Ajuste de entrega']

    # Cobertura mínima (dias)
    # O Excel usa ROUND() que arredonda x.5 sempre para cima.
    # O Python round() usa banker's rounding (x.5 arredonda para par).
    # Para replicar o Excel: adicionar epsilon antes de int() quando o residual é exatamente .5.
    def excel_round(x):
        """Arredondamento matemático (0.5 → cima), compativel com ROUND() do Excel."""
        return float(math.floor(x + 0.5))

    res['Cobertura mínima (dias)'] = (
        est_seg_dias * (1.0 + res['Fator de ajuste']) + res['Prazo cadastrado']
    ).apply(excel_round)

    # Dias de ajuste
    res['Dias de ajuste'] = res['Cobertura mínima (dias)'] - (est_seg_dias + res['Prazo cadastrado'])

    # Dif est-cob
    dif_est_list = []
    for idx, r in res.iterrows():
        cob = r['Cobertura mínima (dias)']
        dsv = r['Dias de saldo virtual']
        if dsv == "-":
            dif_est_list.append(np.round(cob))
        else:
            dif_est_list.append(np.round(cob - float(dsv)))
    res['Dif est-cob'] = dif_est_list

    # Valor unitário
    res['Valor unitário'] = df_apoio['Valor Unitário'] if 'Valor Unitário' in df_apoio.columns else 0.0

    # Faixa de compra
    faixa_list = []
    for idx, r in res.iterrows():
        fam = r['Familia']
        v_unit = r['Valor unitário']
        c_dia = r['Cons diário']
        if fam == "LAM":
            faixa_list.append("B")
        elif v_unit * 90.0 * c_dia <= teto_compra:
            faixa_list.append("C")
        elif v_unit * 30.0 * c_dia <= teto_compra:
            faixa_list.append("B")
        else:
            faixa_list.append("A")
    res['Faixa de compra'] = faixa_list

    # Repres. De cons. Mensal
    res['Repres. De cons. Mensal'] = res['Valor unitário'] * res['Cons diário'] * 30.0

    # % Cons. / período
    tot_repres = res['Repres. De cons. Mensal'].sum()
    res['% Cons. / período'] = res['Repres. De cons. Mensal'] / tot_repres if tot_repres != 0 else 0.0

    # Ponto de pedido
    ponto_list = []
    for idx, r in res.iterrows():
        desc_str = str(r['Desc'])
        first_char = desc_str[0] if len(desc_str) > 0 else ''
        sv = r['Saldo virtual']
        st = r['Status']
        dsv = r['Dias de saldo virtual']
        cob = r['Cobertura mínima (dias)']

        if first_char == '#' and sv > 0:
            ponto_list.append("ok")
        elif st == "Z":
            ponto_list.append("ok")
        elif dsv != "-" and float(dsv) <= cob + 7.0:
            ponto_list.append("comprar")
        else:
            ponto_list.append("ok")
    res['Ponto de pedido'] = ponto_list

    # Sugestão de compra (dias)
    sug_list = []
    for idx, r in res.iterrows():
        pp = r['Ponto de pedido']
        if pp == "ok":
            sug_list.append(0.0)
        else:
            fx = r['Faixa de compra']
            cob = r['Cobertura mínima (dias)']
            dsv = float(r['Dias de saldo virtual'])
            dias_cob = capa_faixas[fx]['Dias_cob']
            ciclo = capa_faixas[fx]['Ciclo_compra']
            val = math.ceil(cob - dsv + dias_cob + ciclo)
            sug_list.append(max(0.0, float(val)))
    res['Sugestão de compra (dias)'] = sug_list

    # Compra com ajuste (dias)
    comp_aj_list = []
    for idx, r in res.iterrows():
        sug = r['Sugestão de compra (dias)']
        if sug == 0:
            comp_aj_list.append(0.0)
        else:
            cob = r['Cobertura mínima (dias)']
            dsv = float(r['Dias de saldo virtual'])
            fx = r['Faixa de compra']
            if cob - dsv > 7:
                rec_max = capa_faixas[fx]['Rec_max']
                ciclo = capa_faixas[fx]['Ciclo_compra']
                dias_cob = capa_faixas[fx]['Dias_cob']
                val = math.ceil((cob - dsv) / rec_max) + ciclo + dias_cob
                comp_aj_list.append(float(val))
            else:
                comp_aj_list.append(sug)
    res['Compra com ajuste (dias)'] = comp_aj_list

    # QTD COMPRA
    res['QTD COMPRA'] = res['Compra com ajuste (dias)'] * res['Cons diário']

    # Decisão de compra
    dec_list = []
    for idx, r in res.iterrows():
        qtd = r['QTD COMPRA']
        l_min = r['Lote min.']
        l_mult = r['Lote mult.']
        if qtd <= 0:
            dec_list.append(0.0)
        elif qtd < l_min:
            dec_list.append(float(l_min))
        else:
            val = l_min + math.ceil((qtd - l_min) / l_mult) * l_mult
            dec_list.append(float(val))
    res['Decisão de compra'] = dec_list

    # VALOR-COMPRA
    res['VALOR-COMPRA'] = res['Decisão de compra'] * res['Valor unitário']



    return res
