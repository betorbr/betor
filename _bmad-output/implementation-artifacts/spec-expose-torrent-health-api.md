---
title: 'Expor saúde de torrents na API'
type: 'feature'
created: '2026-08-31'
status: 'done'
baseline_commit: '54241e4d27ae0fe54679e223833f82a2dc75e5a0'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Os dados de saúde de torrents já são persistidos no `Item`, mas não fazem parte do `ItemSchema` usado pelas respostas da API. Clientes não conseguem identificar o histórico de falhas, a quantidade de dias afetados ou se um torrent está morrendo ou morto.

**Approach:** Ampliar o schema de resposta de itens com o histórico e os três campos derivados já definidos no domínio. Validar a exposição por meio de teste de contrato/serialização, mantendo os endpoints existentes e a compatibilidade com documentos antigos.

## Boundaries & Constraints

**Always:** `ItemSchema` deve expor `torrent_failure_history`, `torrent_failure_days`, `torrent_is_dying` e `torrent_is_dead` com os tipos correspondentes aos contratos de `betor.entities`. As respostas de listagem e detalhe devem herdar essa exposição por continuarem usando `ItemSchema`. Os valores persistidos devem ser retornados sem recalcular ou transformar a semântica definida pelo repositório.

**Ask First:** Nenhuma decisão adicional prevista; os novos campos devem manter o comportamento dos campos existentes de `ItemSchema` e não devem preencher valores padrão quando ausentes.

**Never:** Não alterar a persistência, o cálculo de saúde, os workers Celery, os parâmetros dos endpoints, a ordenação ou os campos já existentes. Não duplicar modelos de falha nem adicionar lógica de negócio ao schema.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Item saudável | Item com histórico vazio, dias `0` e flags falsas | `ItemSchema.model_validate()` e a resposta JSON incluem os quatro campos com seus valores | Nenhum |
| Item em deterioração | Item com registros e `torrent_failure_days >= 1` | Histórico preservado, contador e flags retornados exatamente como persistidos | Nenhum |
| Documento incompleto | Item sem qualquer um dos quatro campos novos | A validação mantém o comportamento dos campos existentes e não inventa valores para campos ausentes | Erro de validação |

</frozen-after-approval>

## Code Map

- `betor/api/v1/items/schemas.py` -- `ItemSchema` é o contrato Pydantic usado como `response_model`; atualmente declara os campos básicos de torrent, mas omite os quatro campos de saúde.
- `betor/entities/item.py` -- `Item` já declara `torrent_failure_history: List[TorrentFailure]`, `torrent_failure_days: int`, `torrent_is_dying: bool` e `torrent_is_dead: bool`; fonte do contrato de domínio.
- `betor/entities/torrent_failure.py` -- define a estrutura tipada de cada registro do histórico e deve ser reutilizada pelo schema.
- `betor/api/v1/items/router.py` -- endpoints de listagem e detalhe usam `response_model=ItemSchema`; não requer alteração.
- `tests/conftest.py` -- fixture de item fornece os quatro campos de saúde persistidos e pode apoiar testes dos consumidores da API, caso necessários.

## Tasks & Acceptance

**Execution:**
- [x] `betor/api/v1/items/schemas.py` -- adicionar os quatro campos de saúde com os tipos/estrutura dos contratos de entidade, sem defaults -- fazer os dados já persistidos chegarem às respostas da API sem preencher valores ausentes.

**Acceptance Criteria:**
- Given um `Item` com histórico e saúde persistidos, when qualquer endpoint de item serializa a entidade, then o JSON contém `torrent_failure_history`, `torrent_failure_days`, `torrent_is_dying` e `torrent_is_dead` com os valores correspondentes.
- Given um documento sem qualquer campo novo, when ele é validado pelo `ItemSchema`, then o schema não preenche valores padrão e mantém o comportamento de validação dos campos existentes.
- Given os endpoints atuais de listagem e detalhe, when suas respostas são geradas, then ambos continuam usando o mesmo contrato e nenhum campo existente ou parâmetro é alterado.

## Design Notes

O schema deve importar e reutilizar `TorrentFailure`, evitando uma segunda definição da estrutura do histórico. Os novos campos não recebem defaults: a API deve refletir a presença dos dados no documento, da mesma forma que os campos existentes de `ItemSchema`, sem mascarar documentos incompletos.

## Verification

**Commands:**
- `poetry run flake8 betor/api/v1/items/schemas.py` -- expected: SUCCESS.
- `poetry run mypy betor/api/v1/items/schemas.py betor/entities/item.py betor/entities/torrent_failure.py` -- expected: SUCCESS.

## Suggested Review Order

**Contrato da API**

- Declara os campos de saúde sem defaults, preservando o comportamento de validação existente.
	[`schemas.py:28`](../../betor/api/v1/items/schemas.py#L28)

- O domínio define a estrutura reutilizada para cada falha registrada.
	[`torrent_failure.py:7`](../../betor/entities/torrent_failure.py#L7)
