# PRD: Migração da API do TMDB para o componente `it-mdb-api`

**Status:** Aprovado & Refinado (Direcionamento de Classes/Módulos Explicitado)  
**Autor:** John (Product Manager)  
**Projeto:** Betor  
**Data:** 2026-11-02  

---

## 1. Visão Geral e Contexto
Atualmente, o Betor realiza chamadas diretas à API oficial do TMDB (`api.themoviedb.org`) para enriquecimento, resolução de IDs externos (IMDb vs. TMDB) e busca textual de títulos. 

Para centralizar o cache, otimizar a performance, reduzir a complexidade de tokens de acesso e evitar limites de taxa (`rate limit`) da API oficial, este documento especifica a substituição completa das integrações com o TMDB pelo componente interno dedicado **`it-mdb-api`** (versão `0.2.0` ou superior).

---

## 2. Objetivos e Metas
* **Desacoplamento:** Remover 100% das dependências de chamadas diretas a `api.themoviedb.org` no código do Betor.
* **Novas Classes e Módulos Dedicados:** Toda a implementação de comunicação com o `it-mdb-api` deve ser feita através de **novas classes e módulos** criados especificamente em `betor/external_apis/`, substituindo os arquivos antigos do TMDB.
* **Centralização de Cache e Rate-Limit:** Aproveitar a arquitetura em cache do `it-mdb-api`, eliminando a necessidade de filas de throttling locais no Celery para o TMDB.
* **Simplificação de Infraestrutura:** Eliminar a necessidade de tokens de acesso ao TMDB (`TMDB_API_ACCESS_TOKEN`).
* **Manutenibilidade:** Manter a integridade de todas as estratégias de processamento e pontuação de itens do Betor intactas, replicando os padrões de requisição já existentes sem adicionar complexidade desnecessária.

---

## 3. Escopo da Solução

### 3.1. O que será construído / modificado
Criação de **novos módulos e classes em `betor/external_apis/`** para consumir os endpoints do `it-mdb-api`:
1. **Busca por ID (IMDb → TMDB / Metadados):**
   * Criar novos adaptadores/classes para consumir os endpoints do `it-mdb-api`:
     * `GET /v1/movies/tt{imdb_id}`
     * `GET /v1/tvshows/tt{imdb_id}`
2. **Obtenção de IDs Externos / Detalhes por TMDB ID:**
   * Criar novos adaptadores/classes para consumir os endpoints do `it-mdb-api`:
     * `GET /v1/movies/{tmdb_id}`
     * `GET /v1/tvshows/{tmdb_id}`
3. **Busca Textual Multicategoria:**
   * Criar novo adaptador/classe para consumir o endpoint do `it-mdb-api`:
     * `GET /v1/search` (Parâmetros: `q`, `language`, `timeout`).

### 3.2. Configurações de Ambiente
* **URL Base:** Criar variável de ambiente/configuração `IT_MDB_API_URL`.
* **Timeout Global:** Criar variável de ambiente/configuração `IT_MDB_API_TIMEOUT` para definir o timeout padrão para todas as interações com o `it-mdb-api`.
* **Remoção:** Remover `TMDBApiSettings` e `TMDB_API_ACCESS_TOKEN`.

### 3.3. Limpeza de Throttling e Fila Celery
* Como o `it-mdb-api` gerencia o cache e o rate-limiting internamente, a fila Celery dedicada a requisições TMDB (`tmdb_api_request`) e sua lógica de throttling associada serão **completamente removidas** e limpas do codebase.

---

## 4. Fora do Escopo (Out of Scope)
* Alterações nas regras de negócio de pontuação e determinação de IDs (`DeterminesIMDbTMDBIdsService`).
* Implementação de código no projeto `it-mdb-api`.

---

## 5. Requisitos Funcionais e Critérios de Aceite

| ID | Requisito | Critério de Aceite |
| :--- | :--- | :--- |
| **RF01** | Novas Classes em `betor/external_apis/` | Toda a integração com o `it-mdb-api` deve residir em **novas classes e módulos** dentro de `betor/external_apis/`, garantindo separação limpa em relação aos adaptadores legados do TMDB. |
| **RF02** | Consulta de Filme/Série por IMDb ID | Dado um `imdb_id`, a nova classe adaptadora deve invocar `GET /v1/movies/tt{imdb_id}` ou `GET /v1/tvshows/tt{imdb_id}` no `it-mdb-api` respeitando o timeout configurado (`IT_MDB_API_TIMEOUT`). |
| **RF03** | Consulta por TMDB ID | Dado um `tmdb_id`, a nova classe adaptadora deve consultar `GET /v1/movies/{tmdb_id}` ou `GET /v1/tvshows/{tmdb_id}` no `it-mdb-api`. |
| **RF04** | Busca Textual por Título e Idioma | A estratégia de busca traduzida deve utilizar a nova classe adaptadora para chamar `GET /v1/search?q={query}&language={language}` no `it-mdb-api`. |
| **RF05** | Variável de Ambiente de Timeout | Deve existir uma configuração/variável de ambiente `IT_MDB_API_TIMEOUT` aplicada a todas as chamadas HTTP para o `it-mdb-api`. |
| **RF06** | Remoção de Fila Celery e Throttling TMDB | A tarefa Celery `tmdb_api_request` e suas configurações de rate limit/fila devem ser removidas do projeto. |
| **RF07** | Limpeza de Credenciais TMDB e Classes Antigas | A variável `TMDB_API_ACCESS_TOKEN`, `TMDBApiSettings` e os módulos antigos baseados na API direta do TMDB em `betor/external_apis/` devem ser removidos. |
