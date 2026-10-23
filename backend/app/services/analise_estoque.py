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
    def _converter_valor_seguro(val):
        if pd.isna(val) or val is None or val == "":
            return 0.0
        if isinstance(val, (int, float, np.number)):
            return float(val)
        s = str(val).strip()
        if not s:
            return 0.0
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except (ValueError, TypeError):
            return 0.0

    for c in num_cols_apoio:
        if c in df_apoio.columns:
            if df_apoio[c].dtype == object:
                df_apoio[c] = df_apoio[c].map(_converter_valor_seguro)
            df_apoio[c] = pd.to_numeric(df_apoio[c], errors="coerce").fillna(0.0)

    # 2. Processamento do histórico de entregas → média de prazo por item
    # Calcula a partir das 5 entregas mais recentes de cada item.
    df_entrega_clean = df_entrega.copy()
    df_entrega_clean.columns = [str(c).strip() for c in df_entrega_clean.columns]
    df_entrega_clean['Item'] = df_entrega_clean['Item'].astype(str).str.strip()

    if 'Data Entrada' in df_entrega_clean.columns and 'Prazo' in df_entrega_clean.columns:
        df_entrega_clean['Data Entrada'] = pd.to_datetime(df_entrega_clean['Data Entrada'], errors='coerce')
        df_entrega_clean['Prazo'] = pd.to_numeric(df_entrega_clean['Prazo'], errors='coerce')
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

    # Média mens + Necessidade (Vetorizado)
    # Excel: IF(Baixa="S", AVERAGEIF(Cons1:Neces,"<>0"), AVERAGEIF(Cons1:Cons4,"<>0")), IFERROR → 0
    # Neces. só entra na média quando Baixa == "S".
    cons_neces_matrix = res[['Cons 1', 'Cons 2', 'Cons 3', 'Cons 4', 'Neces.']].values
    mask_s = (baixa == "S").values
    valid_cols = np.ones(cons_neces_matrix.shape, dtype=bool)
    valid_cols[:, 4] = mask_s
    is_nz = (cons_neces_matrix != 0) & valid_cols
    count_nz = is_nz.sum(axis=1)
    sum_nz = np.where(is_nz, cons_neces_matrix, 0.0).sum(axis=1)
    safe_count = np.where(count_nz == 0, 1, count_nz)
    res['Média mens + Necessidade'] = np.where(count_nz > 0, sum_nz / safe_count, 0.0)

    # Analisar e Status (Vetorizado)
    desc_series = res['Desc'].str.strip()
    starts_hash = desc_series.str.startswith('#').values
    starts_special = (starts_hash | desc_series.str.startswith('$') | desc_series.str.startswith('~*')).values

    saldo = res['Saldo virtual'].values
    neces = res['Neces.'].values
    media_neces = res['Média mens + Necessidade'].values

    # Status
    c14_mat = res[['Cons 1', 'Cons 2', 'Cons 3', 'Cons 4']].values
    zeros_c14 = (c14_mat == 0).sum(axis=1)

    cond_st_z1 = starts_hash & (saldo >= 0)
    cond_st_yat = starts_special
    cond_st_x = (zeros_c14 == 0)
    cond_st_z2 = (zeros_c14 == 4) & (neces == 0) & (saldo > 0)

    status_arr = np.select(
        [cond_st_z1, cond_st_yat, cond_st_x, cond_st_z2],
        ["Z", "Y@", "X", "Z"],
        default="Y"
    )
    res['Status'] = status_arr

    # Analisar
    mat_nz = np.where(cons_neces_matrix == 0, np.inf, cons_neces_matrix)
    min_nz = mat_nz.min(axis=1)
    min_non_zero = np.where(np.isinf(min_nz), 0.0, min_nz)
    max_val = cons_neces_matrix.max(axis=1)

    diff1 = np.abs(max_val - media_neces)
    diff2 = np.abs(min_non_zero - media_neces)
    max_diff = np.maximum(diff1, diff2)

    cond_an_1 = saldo <= media_neces
    cond_an_2 = starts_special
    cond_an_zero = media_neces == 0
    safe_media = np.where(media_neces == 0, 1.0, media_neces)
    cond_an_3 = (max_diff / safe_media) > 0.7

    analisar_arr = np.select(
        [cond_an_1 | cond_an_2, cond_an_zero, cond_an_3],
        ["ANALIZAR", "ANALIZAR#", "ANALIZAR"],
        default="-"
    )
    res['Analisar'] = analisar_arr

    # Indice de consumo (Vetorizado)
    mask_calc_ind = ~np.isin(status_arr, ['Y', 'Z'])
    c1 = c14_mat[:, 0]
    c4 = c14_mat[:, 3]
    avg_c = c14_mat.mean(axis=1)
    max_c = c14_mat.max(axis=1)
    min_c = c14_mat.min(axis=1)
    safe_avg_c = np.where(avg_c == 0, 1.0, avg_c)

    ind_cons = np.where(
        mask_calc_ind & (avg_c != 0),
        ((c4 - c1) / safe_avg_c) * (1.0 + (max_c - min_c) / safe_avg_c),
        0.0
    )
    res['Indice de consumo'] = ind_cons

    # Ajuste cons (Vetorizado)
    res['Ajuste cons'] = np.select(
        [ind_cons < -1, ind_cons < -0.2, ind_cons <= 0.2, ind_cons <= 1.3],
        [-0.3, -0.1, 0.0, 0.2],
        default=0.3
    )

    # Indice futuro (Vetorizado)
    avg_c4_val = avg_cons4.values
    denom_fut = 1.0 + avg_c4_val
    ind_fut = np.where(denom_fut == 0, 1.0, (1.0 + neces) / denom_fut)
    res['Indice futuro'] = ind_fut

    val_fut = np.round(ind_fut, 6)
    res['Ajuste futuro'] = np.select(
        [(val_fut >= 0.8) & (val_fut <= 1.2), val_fut > 1.2, val_fut < 0.8],
        [0.0, 0.2, -0.2],
        default=0.0
    )

    # Indice de entrega (Vetorizado)
    m_ent = res['Média prazos de entrega (5 - 3 últimos)'].values
    p_cad = res['Prazo cadastrado'].values
    safe_pcad = np.where(p_cad == 0, 1.0, p_cad)
    ind_ent = np.where(p_cad == 0, 0.0, m_ent / safe_pcad)
    res['Indice de entrega'] = ind_ent
    res['Ajuste de entrega'] = ind_ent - 1.0

    # Fator de ajuste & Cobertura mínima (Vetorizado)
    res['Fator de ajuste'] = res['Ajuste cons'] + res['Ajuste futuro'] + res['Ajuste de entrega']
    val_cob = est_seg_dias * (1.0 + res['Fator de ajuste'].values) + p_cad
    res['Cobertura mínima (dias)'] = np.floor(val_cob + 0.5).astype(float)
    res['Dias de ajuste'] = res['Cobertura mínima (dias)'] - (est_seg_dias + p_cad)

    # Dif est-cob (Vetorizado)
    dsv_vals = res['Dias de saldo virtual'].values
    dsv_is_dash = (dsv_vals == "-")
    dsv_float = np.array([float(x) if x != "-" else 0.0 for x in dsv_vals])
    cob = res['Cobertura mínima (dias)'].values
    res['Dif est-cob'] = np.where(dsv_is_dash, np.round(cob), np.round(cob - dsv_float))

    # Faixa de compra (Vetorizado)
    res['Valor unitário'] = df_apoio['Valor Unitário'] if 'Valor Unitário' in df_apoio.columns else 0.0
    fam = res['Familia'].values
    v_unit = res['Valor unitário'].values
    c_dia = res['Cons diário'].values
    cond_b1 = (fam == "LAM")
    cond_c = (v_unit * 90.0 * c_dia <= teto_compra)
    cond_b2 = (v_unit * 30.0 * c_dia <= teto_compra)
    res['Faixa de compra'] = np.select([cond_b1, cond_c, cond_b2], ["B", "C", "B"], default="A")

    # Repres. De cons. Mensal & % Cons. / período
    res['Repres. De cons. Mensal'] = res['Valor unitário'] * res['Cons diário'] * 30.0
    tot_repres = res['Repres. De cons. Mensal'].sum()
    res['% Cons. / período'] = res['Repres. De cons. Mensal'] / tot_repres if tot_repres != 0 else 0.0

    # Ponto de pedido (Vetorizado)
    cond_ok1 = starts_hash & (saldo > 0)
    cond_ok2 = (status_arr == "Z")
    cond_comprar = (~dsv_is_dash) & (dsv_float <= cob + 7.0)
    res['Ponto de pedido'] = np.select([cond_ok1, cond_ok2, cond_comprar], ["ok", "ok", "comprar"], default="ok")

    # Sugestão de compra (dias) (Vetorizado)
    dias_cob_map = {k: float(v['Dias_cob']) for k, v in capa_faixas.items()}
    ciclo_map = {k: float(v['Ciclo_compra']) for k, v in capa_faixas.items()}
    rec_max_map = {k: float(v['Rec_max']) for k, v in capa_faixas.items()}

    fc_series = res['Faixa de compra']
    dias_cob_arr = fc_series.map(dias_cob_map).fillna(0.0).values
    ciclo_arr = fc_series.map(ciclo_map).fillna(0.0).values
    rec_max_arr = fc_series.map(rec_max_map).fillna(1.0).values
    rec_max_safe = np.where(rec_max_arr == 0, 1.0, rec_max_arr)

    val_sug = np.ceil(cob - dsv_float + dias_cob_arr + ciclo_arr)
    sug_arr = np.where(res['Ponto de pedido'] == "ok", 0.0, np.maximum(0.0, val_sug))
    res['Sugestão de compra (dias)'] = sug_arr

    # Compra com ajuste (dias) (Vetorizado)
    cond_aj = (sug_arr != 0) & ((cob - dsv_float) > 7)
    val_aj = np.ceil((cob - dsv_float) / rec_max_safe) + ciclo_arr + dias_cob_arr
    comp_aj = np.where(sug_arr == 0, 0.0, np.where(cond_aj, val_aj, sug_arr))
    res['Compra com ajuste (dias)'] = comp_aj

    # QTD COMPRA
    res['QTD COMPRA'] = (res['Compra com ajuste (dias)'] * res['Cons diário']).round(3)

    # Decisão de compra & VALOR-COMPRA (Vetorizado)
    qtd = res['QTD COMPRA'].values
    l_min_val = res['Lote min.'].values
    l_mult_val = res['Lote mult.'].values
    l_mult_safe = np.where(l_mult_val == 0, 1.0, l_mult_val)

    cond_dec_zero = qtd <= 0
    cond_dec_lmin = qtd < l_min_val
    val_mult = l_min_val + np.ceil((qtd - l_min_val) / l_mult_safe) * l_mult_safe

    dec_compra = np.select([cond_dec_zero, cond_dec_lmin], [0.0, l_min_val], default=val_mult)
    res['Decisão de compra'] = dec_compra
    res['VALOR-COMPRA'] = (dec_compra * res['Valor unitário'].values).round(3)

    numeric_cols = res.select_dtypes(include=[np.number]).columns
    res[numeric_cols] = res[numeric_cols].round(3)

    return res
