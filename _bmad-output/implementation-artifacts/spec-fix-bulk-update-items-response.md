---
title: 'Corrigir resposta e contagens do bulk update de items'
type: bugfix
created: '2026-08-31'
status: 'done'
baseline_commit: '61163e9a735bd3915309bf7ac0f4cf706a52864e'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A resposta de `POST /v1/admin/bulk-update-items/` calcula `excluded_count` e `total_available` sobre consultas limitadas e materializa items apenas para contá-los, então os números não representam todos os items e o consumo de memória cresce com a coleção. Além disso, `task_ids` não informa qual item originou cada tarefa.

**Approach:** Usar `count_documents` para contar diretamente os items recentes e os items elegíveis, sem carregar esses conjuntos em memória. Aplicar `limit` somente ao `find` dos items elegíveis que serão despachados e substituir `task_ids` por `updated_items`, uma lista com `task_id` e `item_id` para cada item despachado.

## Boundaries & Constraints

**Always:** `filtered_count` conta via `count_documents` todos os items atualizados dentro da janela de exclusão; `remaining_count` conta via `count_documents` todos os items que passam pelo filtro e ainda podem ser processados; `processed_count` conta apenas os items efetivamente despachados, respeitando `limit`; somente os items despachados são materializados; a ordenação por `updated_at` DESC e o despacho de uma tarefa por item permanecem; cada entrada de `updated_items` contém `task_id` e `item_id` correspondentes.

**Ask First:** Nenhuma decisão adicional conhecida.

**Never:** Não alterar a tarefa Celery individual, as regras de atualização de torrent, os parâmetros de entrada ou o comportamento de ordenação; não usar `find` sem `limit` para obter contagens; não manter `task_ids` como campo de resposta compatível.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH | 10 items elegíveis e 4 items atualizados dentro da janela; `limit=1` | `filtered_count=4`, `remaining_count=10`, `processed_count=1`, `updated_items` com 1 par de IDs; contagens feitas por `count_documents` | N/A |
| NO_ELIGIBLE_ITEMS | Nenhum item passa pelo filtro | `filtered_count` reflete os recentes, `remaining_count=0`, `processed_count=0`, `updated_items=[]` | N/A |
| NO_RECENT_ITEMS | Nenhum item está dentro da janela de exclusão | `filtered_count=0`; `remaining_count` reflete todos os elegíveis | N/A |
| ZERO_EXCLUSION_DAYS | `exclude_updated_within_days=0` | Nenhum item é filtrado por janela; `filtered_count=0` e `remaining_count` conta todos os items elegíveis | N/A |

</frozen-after-approval>

## Code Map

- `betor/services/bulk_update_items_service.py` -- calcula queries de contagem, busca somente items elegíveis limitados e associa IDs das tarefas aos items.
- `betor/api/v1/admin/bulk_update_items_schemas.py` -- define `BulkUpdateItemsResponse`, contrato Pydantic que deve substituir `task_ids` e renomear os contadores.
- `betor/api/v1/admin/router.py` -- registra o endpoint e usa o schema de resposta; não deve exigir mudança de fluxo.
- `tests/betor/services/test_bulk_update_items_service.py` -- testes unitários do serviço; os mocks precisam verificar `count_documents`, ausência de `find` ilimitado, limite da busca de despacho e o novo payload.
- `_bmad-output/patterns/CELERY_TASK_DISPATCH_SIGNATURE_PATTERN.md` -- padrão existente de despacho por `celery_app.signature()` que deve ser preservado.

## Tasks & Acceptance

**Execution:**
- [ ] `betor/api/v1/admin/bulk_update_items_schemas.py` -- substituir `task_ids` por uma lista tipada de objetos com `task_id` e `item_id`, e expor `filtered_count` e `remaining_count` -- alinhar o contrato com a nova resposta.
- [ ] `betor/services/bulk_update_items_service.py` -- usar `count_documents` para as contagens, buscar com `sort` e `limit` apenas os items a despachar e construir `updated_items` -- corrigir a semântica dos totais sem carregar a coleção inteira.
- [ ] `tests/betor/services/test_bulk_update_items_service.py` -- cobrir contagens por `count_documents`, limite da busca, ausência de elegíveis, zero dias e associação entre IDs -- impedir regressões no contrato, performance e casos-limite.

**Acceptance Criteria:**
- Given items recentes e antigos, when o endpoint é chamado com um `limit` menor que os totais, then `filtered_count` e `remaining_count` continuam representando todos os items dos respectivos conjuntos.
- Given items elegíveis, when tarefas são despachadas, then `processed_count` é igual ao tamanho de `updated_items`, e cada objeto contém o `item_id` despachado e o `task_id` retornado pelo Celery.
- Given nenhum item elegível, when o serviço é executado, then `processed_count` é zero e `updated_items` é uma lista vazia sem erro.
- Given a resposta do endpoint, when validada pelo schema, then os campos antigos `task_ids`, `excluded_count` e `total_available` não são necessários nem retornados.
- Given uma coleção com muitos items, when as contagens são calculadas, then `count_documents` é usado e nenhum cursor ilimitado é iterado apenas para contar.

## Spec Change Log

## Verification

**Commands:**
- `poetry run pytest tests/betor/services/test_bulk_update_items_service.py -v` -- expected: all focused service tests pass, including count and zero-day cases.
- `poetry run flake8 betor/api/v1/admin/bulk_update_items_schemas.py betor/services/bulk_update_items_service.py tests/betor/services/test_bulk_update_items_service.py` -- expected: no lint errors.

## Suggested Review Order

**Contagens e despacho**

- `count_documents` separa itens recentes dos elegíveis sem materializar a coleção.
	[`bulk_update_items_service.py:29`](../../betor/services/bulk_update_items_service.py#L29)

- O limite é aplicado somente ao lote ordenado que será despachado.
	[`bulk_update_items_service.py:47`](../../betor/services/bulk_update_items_service.py#L47)

**Contrato de resposta**

- A resposta associa cada tarefa Celery ao item atualizado.
	[`bulk_update_items_schemas.py:17`](../../betor/api/v1/admin/bulk_update_items_schemas.py#L17)

- Os contadores expõem filtrados, restantes e processados com semântica distinta.
	[`bulk_update_items_schemas.py:24`](../../betor/api/v1/admin/bulk_update_items_schemas.py#L24)

**Verificação**

- Os testes cobrem limites, ausência de elegíveis, zero dias e operadores de data.
	[`test_bulk_update_items_service.py:76`](../../tests/betor/services/test_bulk_update_items_service.py#L76)
