---
modulo: "Extrator_PCP"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, infra, python, scraping, multi-threading, requests]
---

# Módulo: Extrator_PCP (backend/app/services/extractor.py)

**Responsabilidade:** Motor de scraping concorrente de alta velocidade localizado em `backend/app/services/extractor.py`. Conecta-se à intranet corporativa (servidor PHP/Apache), gerencia autenticação individual por thread para evitar conflitos de sessão (`PHPSESSID`), distribui tarefas de coleta em pool de até 20 workers e extrai tabelas HTML diretamente para DataFrames Pandas.

## Principais Funções / Métodos
* `login()`: Executa handshake HTTP de autenticação com o formulário do PCP e valida o cookie de sessão.
* `gerar_tarefas(analise)`: Constrói a lista de requisições necessárias (`apoio_compras`, `ordens`, `cons`, `estoque`, `conf`, `apont`) com base nas famílias e locais de fabricação.
* `executar_paralelo(tarefas, max_workers=20)`: Gerencia a fila thread-safe (`queue.Queue`) e orquestra o pool de threads com cálculo de média móvel de tempo persistido em `settings.TEMPOS_FILE` (`backend/data/tempos_execucao.json`).
* `_extract_table(html)`: Parser tolerante em BeautifulSoup para converter tags `<table>` em DataFrames Pandas.
* `salvar_html(conteudo, nome_base)`: Persiste arquivos HTML de diagnóstico em `settings.DATA_DIR / "saida_html"`.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[04-Infra-Dados/Pipeline_Coleta]]

**➡️ Quem este módulo chama (Saída/Uso):**
* [[04-Infra-Dados/Configuracoes_Settings]]
* **Bibliotecas Externas:** `requests`, `pandas`, `beautifulsoup4`, `threading`, `queue`.
