---
script: "backend/app/feriados.py"
tipo: "automacao"
linguagem: "python"
gatilho: "manual"
data_atualizacao: 2026-10-14
tags: [automacao, script, python, feriados, crawler]
---

# Automação: backend/app/feriados.py

**Objetivo:** Automação para crawler e extração de todos os feriados corporativos e dias não úteis registrados no sistema ERP PCP para os anos de 2025, 2026 e 2027, salvando a lista no arquivo `backend/app/feriados.txt`.

## Como é Executado (Gatilho)

- Executado interativamente no terminal via comando:
  ```powershell
  python backend/app/feriados.py
  ```
- Solicita usuário e senha interativamente via `input()` e `getpass()`.

## Fluxo de Execução

1. Inicializa sessão HTTP com o sistema PCP em `http://192.168.0.6` e efetua login com as credenciais fornecidas.
2. Calcula o calendário de dias de semana (segunda a sexta) para os anos de 2025, 2026 e 2027.
3. Para cada dia útil de calendário, faz requisição GET para `/pcp/feriados.php?dat_ref=YYYY-MM-DD`.
4. Identifica dias onde a situação indica feriado (`ies_situa == '3'`) e armazena na lista de feriados.
5. Ordena as datas de forma crescente e grava no arquivo de texto `backend/app/feriados.txt`.

## Arquivos Afetados

**➡️ Modifica/Lê:**
* `backend/app/feriados.txt`
* [[04-Infra-Dados/Configuracoes_Settings]]
