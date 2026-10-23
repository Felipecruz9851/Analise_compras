---
modulo: "Configuracoes_Settings"
tipo: "infra"
linguagem: "python"
data_atualizacao: 2026-10-14
tags: [codigo, infra, python, configuracoes, constantes, caminhos]
---

# Módulo: Configuracoes_Settings (backend/app/settings.py, backend/app/services/config_parametros.json)

**Responsabilidade:** Repositório central de parâmetros operacionais, mapeamento de grupos de materiais (`FAMILIAS`), locais de manufatura fabril (`LOCAIS`), prazos logísticos por representante, leitura de feriados oficiais e resolução centralizada de caminhos do sistema.

## Principais Funções / Métodos e Constantes de Caminho
* `BASE_DIR`, `DATA_DIR`, `CSV_DIR`, `EXPORTS_DIR`, `SNAPSHOTS_DIR`: Constantes `Path` que garantem que todos os módulos acessem as pastas de dados (`backend/data/`) independentemente do diretório de execução (CWD).
* `CONFIG_PARAMETROS`: Caminho absoluto para `backend/app/services/config_parametros.json`.
* `TEMPOS_FILE`: Caminho para `backend/data/tempos_execucao.json`.
* `carregar_feriados()`: Lê o arquivo `backend/app/feriados.txt` e converte em lista de objetos `datetime.date`.
* `carregar_familias()`: Carrega e normaliza os vínculos de produtos do arquivo `backend/app/familias.csv`.
* `prazo_por_representante(rep)`: Mapeador que retorna o lead time de expedição de acordo com o código do representante.

## Dependências (Grafo)
**⬅️ Quem chama este módulo (Entrada):**
* [[02-Backend-API/Main_Server]]
* [[02-Backend-API/API_Router]]
* [[04-Infra-Dados/Extrator_PCP]]
* [[04-Infra-Dados/Pipeline_Coleta]]
* [[03-Dominio-Calculos/Regra_Compra_Necessidade]]
* [[05-Automacoes/Script_Carrega_Dados]]

**➡️ Quem este módulo chama (Saída/Uso):**
* `backend/app/feriados.txt`, `backend/app/familias.csv`, `backend/app/services/config_parametros.json`
* **Bibliotecas Externas:** `pathlib`, `csv`, `pandas`.
