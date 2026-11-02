# Especificação Técnica (SPEC): Migração da API do TMDB para `it-mdb-api`

**Status:** Aprovado para Desenvolvimento (Novas Classes e Módulos em `betor/external_apis/`)  
**Autor:** John (Product Manager)  
**Projeto:** Betor  
**Referência PRD:** `_bmad-output/planning-artifacts/prds/prd-migration-tmdb-to-it-mdb-api/prd.md`

---

## 1. Visão Geral das Histórias (User Stories)

Dividimos a migração em 4 histórias independentes e incrementais que devem ser executadas pelo time de desenvolvimento, utilizando **novas classes e módulos** criados em `betor/external_apis/`:

1. **ST-01: Configuração de Ambiente e Novas Classes Adaptadoras para o `it-mdb-api`**
   - Criar as configurações `IT_MDB_API_URL` e `IT_MDB_API_TIMEOUT`.
   - Criar os novos módulos/classes em `betor/external_apis/` (ex: `itmdb_api.py` ou arquivos equivalentes dedicados) para interagir com o `it-mdb-api`.
   - Remover as configurações e módulos legados do TMDB.
2. **ST-02: Implementação de Busca por ID (IMDb ⇄ TMDB) com `it-mdb-api`**
   - Implementar nas novas classes os métodos para consumir os endpoints `/v1/movies/tt{imdb_id}`, `/v1/tvshows/tt{imdb_id}`, `/v1/movies/{tmdb_id}` e `/v1/tvshows/{tmdb_id}`.
3. **ST-03: Implementação de Busca Textual Multi com `GET /v1/search`**
   - Implementar nas novas classes o método de busca textual consumindo `GET /v1/search` com suporte a `q`, `language` e `timeout`.
4. **ST-04: Remoção da Fila Celery, Lógica de Rate Limit e Módulos Antigos do TMDB**
   - Remover a task Celery `tmdb_api_request`, a fila `api-requests` e os arquivos antigos de integração com `api.themoviedb.org`.

---

## 2. Detalhamento Técnico por História (HOW)

### ST-01: Configuração e Novas Classes em `betor/external_apis/`
* **Settings (`betor/settings.py`):**
  - Remover `TMDBApiSettings` e `tmdb_api_settings`.
  - Adicionar `ITMDBApiSettings`:
    ```python
    class ITMDBApiSettings(BaseSettings):
        url: str = Field(default="http://localhost:8000", alias="it_mdb_api_url")
        timeout: int = Field(default=30, alias="it_mdb_api_timeout")
        model_config = {"env_file": ".env", "extra": "allow"}
    
    itmdb_api_settings = ITMDBApiSettings()
    ```
* **Nova Estrutura em `betor/external_apis/`:**
  - Criar novos arquivos limpos (ex: `betor/external_apis/itmdb_api.py` ou classes dedicadas) que encapsulam as chamadas HTTP assíncronas (`httpx.AsyncClient`) para o `it-mdb-api` utilizando o timeout global definido em `itmdb_api_settings.timeout`.

### ST-02, ST-03 e ST-04: Refatoração dos Adaptadores e Limpeza
* Conectar as estratégias do Betor (`TmdbFindByImdbStrategy`, `ImdbFindByTmdbStrategy`, `TmdbTranslatedTitleSearchStrategy`, etc.) para instanciar e utilizar exclusivamente as **novas classes** de `betor/external_apis/`.
* Remover completamente os arquivos legados (`tmdb_find_by_id_api.py`, `tmdb_external_ids_api.py`, `tmdb_search_multi_api.py`, `tmdb_trending_api.py`).
* Remover a task Celery `tmdb_api_request` e suas rotas de fila.

---

## 3. Critérios de Aceite Globais (Acceptance Criteria)

- [ ] Novas classes e módulos criados em `betor/external_apis/` para todas as interações com o `it-mdb-api`.
- [ ] Variáveis de ambiente implementadas: `IT_MDB_API_URL` e `IT_MDB_API_TIMEOUT`.
- [ ] Módulos antigos do TMDB (`tmdb_*.py`) e a task Celery `tmdb_api_request` completamente removidos.
- [ ] Testes unitários e de aceitação atualizados e passando com sucesso (`poetry run pytest tests` e `poetry run pytest acceptance_tests`).
