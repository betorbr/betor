# Relatório de Mapeamento e Migração: Remoção da API do TMDB para `it-mdb-api`

Este documento detalha o mapeamento atualizado das dependências do projeto **Betor** em relação à API oficial do TMDB (`api.themoviedb.org`), cruzando com o contrato OpenAPI atualizado do componente **`it-mdb-api`** (versão `0.2.0`) disponível em `@docs/it-mdb-api-openapi.json`.

---

## 1. Mapeamento de Funcionalidades e Endpoints do TMDB utilizados pelo Betor vs. `it-mdb-api`

O Betor consome a `api.themoviedb.org` através de 3 vertentes principais em `betor/external_apis/`. Todas elas possuem equivalentes diretos implementados no `it-mdb-api`:

### 1.1. Busca por ID Externo (`TMDBFindByIdAPI`)
* **URL Atual no Betor:** `https://api.themoviedb.org/3/find/{external_id}?external_source={external_source}`
* **Uso no Betor:** Nas estratégias `TmdbFindByImdbStrategy` e `ProviderURLMappingStrategy` (busca por `imdb_id`).
* **Equivalente no `it-mdb-api`:**
  * `GET /v1/movies/tt{imdb_id}`
  * `GET /v1/tvshows/tt{imdb_id}`
* **Status:** ✅ **Disponível**

### 1.2. IDs Externos a partir do TMDB ID (`TMDBExternalIdsAPI`)
* **URL Atual no Betor:** `https://api.themoviedb.org/3/{item_type}/{tmdb_id}/external_ids`
* **Uso no Betor:** Na estratégia `ImdbFindByTmdbStrategy` (obtenção de `imdb_id` a partir do `tmdb_id`).
* **Equivalente no `it-mdb-api`:**
  * `GET /v1/movies/{tmdb_id}`
  * `GET /v1/tvshows/{tmdb_id}`
  *(Os schemas `MovieV1` e `TVShowV1` retornam detalhadamente tanto o `tmdb_id` quanto o `imdb_id`).*
* **Status:** ✅ **Disponível**

### 1.3. Busca Multicategoria por Título / Idioma (`TMDBSearchMultiAPI`)
* **URL Atual no Betor:** `https://api.themoviedb.org/3/search/multi?query={query}&language={language}`
* **Uso no Betor:** Na estratégia `TmdbTranslatedTitleSearchStrategy` (busca textual com suporte a `pt-BR`).
* **Equivalente no `it-mdb-api`:**
  * `GET /v1/search` (Parâmetros: `q`, `language`, `timeout`). Retorna uma lista de `SearchItemV1` contendo ID, títulos, ano, visão geral, pôster, backdrop, `imdb_id`, `tmdb_id` e `media_type`.
* **Status:** ✅ **Disponível**

---

## 2. Matriz de Cobertura (Gap Analysis Atualizada)

| Funcionalidade no Betor | Endpoint TMDB Original | Endpoint no `it-mdb-api` (`v0.2.0`) | Status |
| :--- | :--- | :--- | :--- |
| **Busca Filme por IMDb ID** | `/3/find/{id}?external_source=imdb_id` | `GET /v1/movies/tt{imdb_id}` | ✅ Concluído |
| **Busca Série por IMDb ID** | `/3/find/{id}?external_source=imdb_id` | `GET /v1/tvshows/tt{imdb_id}` | ✅ Concluído |
| **Detalhes / IDs de Filme** | `/3/movie/{id}/external_ids` | `GET /v1/movies/{tmdb_id}` | ✅ Concluído |
| **Detalhes / IDs de Série** | `/3/tv/{id}/external_ids` | `GET /v1/tvshows/{tmdb_id}` | ✅ Concluído |
| **Busca Textual Multi** | `/3/search/multi?query=...` | `GET /v1/search?q=...&language=...` | ✅ Concluído |

---

## 3. Conclusão
Com a implementação do endpoint `GET /v1/search/` e a atualização do contrato OpenAPI em `@docs/it-mdb-api-openapi.json`, **100% das dependências da `api.themoviedb.org` utilizadas pelo Betor estão cobertas pelo `it-mdb-api`**.
