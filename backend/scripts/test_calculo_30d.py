import pickle
from pathlib import Path
import sys
import pandas as pd
import numpy as np

# Adiciona o diretório do backend ao sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.purchase_logic import calcular_com_apoio_30
from app.session_manager import SessionState
from app.api import aplicar_30d_em_massa, restaurar_edicoes_em_massa, obter_slice

def run_tests():
    print("--- INICIANDO TESTES DO CÁLCULO DE 30 DIAS ---")
    
    # 1. Carrega snapshot real para teste
    pkl_path = backend_dir / "data" / "snapshots" / "snapshot_Geral.pkl"
    if not pkl_path.exists():
        pkl_path = backend_dir / "snapshot_Geral.pkl"
    
    if not pkl_path.exists():
        print(f"ERRO: Snapshot {pkl_path} não encontrado.")
        return

    with open(pkl_path, "rb") as f:
        dfs = pickle.load(f)
        
    print(f"Snapshot carregado com sucesso. Tabelas: {list(dfs.keys())}")
    
    # 2. Teste Fallback: Sem a coluna 'Neces (30 dias)'
    print("\n[Teste 1] Teste de Fallback (sem coluna 'Neces (30 dias)')...")
    # Garante que não tem a coluna
    if "Neces (30 dias)" in dfs["apoio_compras"].columns:
        dfs["apoio_compras"] = dfs["apoio_compras"].drop(columns=["Neces (30 dias)"])
        
    df_result_fallback = calcular_com_apoio_30("Geral", dfs)
    assert not any(c.endswith("_N30") for c in df_result_fallback.columns), "Erro: Não deveria ter colunas _N30 no fallback!"
    print("[OK] Fallback funcionou perfeitamente. Nenhuma coluna _N30 gerada.")

    # 3. Teste com 'Neces (30 dias)'
    print("\n[Teste 2] Teste com coluna 'Neces (30 dias)' presente...")
    # Cria uma coluna sintética de teste: 50% da necessidade geral
    dfs_com_30 = dfs.copy()
    df_apoio = dfs["apoio_compras"].copy()
    
    neces_num = pd.to_numeric(
        df_apoio["Neces"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
        errors="coerce"
    ).fillna(0.0)
    
    df_apoio["Neces (30 dias)"] = (neces_num * 0.5).round(2)
    dfs_com_30["apoio_compras"] = df_apoio
    
    df_result_30 = calcular_com_apoio_30("Geral", dfs_com_30)
    
    colunas_n30_encontradas = [c for c in df_result_30.columns if c.endswith("_N30")]
    print(f"Colunas _N30 encontradas: {colunas_n30_encontradas}")
    assert "Decis Compras_N30" in df_result_30.columns, "Erro: Decis Compras_N30 ausente!"
    assert "Falta_N30" in df_result_30.columns, "Erro: Falta_N30 ausente!"
    assert len(df_result_30) == len(df_result_fallback), "Erro: Divergência no tamanho do DataFrame!"
    print("[OK] Calculo de 30 dias executado com sucesso e colunas _N30 geradas e alinhadas.")

    # 4. Teste das funções de API e Sessão (aplicar_30d_em_massa e restaurar_edicoes_em_massa)
    print("\n[Teste 3] Teste de Ações em Massa (Session / API)...")
    session = SessionState()
    # Atribui __rowId
    df_result_30["__rowId"] = [f"row-{i}" for i in range(len(df_result_30))]
    session.df_ativo = df_result_30
    session.df_base = df_result_30
    session.analise_nome = "Geral"

    # Aplica em massa
    res_aplicar = aplicar_30d_em_massa(session)
    print(f"Resultado aplicar_30d_em_massa: {res_aplicar}")
    assert res_aplicar.get("status") == "ok", "Erro ao aplicar em massa"
    assert len(session.edicoes) == len(df_result_30), "Erro: Total de edições difere do tamanho da tabela"

    # Testa obter_slice com as edições aplicadas
    slice_resp = obter_slice(session, {"start": 0, "size": 10})
    assert slice_resp.get("has_30d") is True, "Erro: has_30d deveria ser True"
    assert "total_geral_n30" in slice_resp, "Erro: total_geral_n30 ausente no slice"
    print(f"Slice obtido: total={slice_resp['total']}, has_30d={slice_resp['has_30d']}, total_geral_n30={slice_resp['total_geral_n30']}")

    # Restaura em massa
    res_restaurar = restaurar_edicoes_em_massa(session)
    print(f"Resultado restaurar_edicoes_em_massa: {res_restaurar}")
    assert res_restaurar.get("status") == "ok", "Erro ao restaurar em massa"
    assert len(session.edicoes) == 0, "Erro: session.edicoes deveria estar vazio após restaurar"
    print("[OK] Acoes em massa e slice testados com 100% de sucesso!")

    print("\n=== TODOS OS TESTES PASSARAM COM SUCESSO! ===")

if __name__ == "__main__":
    run_tests()
