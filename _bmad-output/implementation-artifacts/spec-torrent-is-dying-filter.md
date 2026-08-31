---
title: 'Filtro opcional por torrent_is_dying nos itens'
type: 'feature'
created: '2026-08-31'
status: 'done'
baseline_commit: '476b2fcbe9e7c76853a90229e4e6cadcb9252d65'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Os endpoints de listagem de itens e de disparo de atualizacoes em massa nao permitem selecionar itens pelo estado persistido `torrent_is_dying`.

**Approach:** Expor um filtro booleano opcional nos dois endpoints e propaga-lo ate as consultas MongoDB. Quando o valor for `true` ou `false`, a consulta deve exigir o valor correspondente; quando omitido ou `None`, nenhuma condicao sobre esse campo deve ser adicionada.

## Boundaries & Constraints

**Always:** Preservar os filtros existentes; tratar `false` como valor explicito e valido; deixar o campo fora da consulta quando for `None`; manter contratos de resposta e limites atuais.

**Ask First:** Nenhuma decisao adicional prevista.

**Never:** Nao alterar a forma como `torrent_is_dying` e calculado ou armazenado; nao transformar `None` em filtro por valores nulos/ausentes; nao alterar endpoints fora de `/v1/items/` e `/v1/admin/bulk-update-items/`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|-----------------------------|----------------|
| HAPPY_PATH_TRUE | `torrent_is_dying=true` no endpoint | A consulta inclui `{"torrent_is_dying": True}` e retorna/processa somente esses itens | N/A |
| HAPPY_PATH_FALSE | `torrent_is_dying=false` no endpoint | A consulta inclui `{"torrent_is_dying": False}` e retorna/processa somente esses itens | N/A |
| OMITTED_OR_NONE | Parametro omitido ou request com valor `None` | Nenhuma clausula `torrent_is_dying` e adicionada; comportamento anterior permanece | N/A |
| COMBINED_FILTERS | Filtro combinado com IDs ou janela de atualizacao | As condicoes existentes e a condicao booleana sao aplicadas em conjunto | N/A |

</frozen-after-approval>

## Code Map

- `betor/api/v1/items/router.py` -- endpoint GET `/v1/items/`; recebe o query param e encaminha filtros para o servico.
- `betor/services/list_items_service.py` -- `ListItemsService.apaginate_params`; compoe `filter_statements` e deve incluir o booleano somente quando nao for `None`.
- `betor/api/v1/admin/bulk_update_items_schemas.py` -- `BulkUpdateItemsRequest`; contrato do corpo POST, atualmente sem o novo campo.
- `betor/api/v1/admin/router.py` -- endpoint POST `/v1/admin/bulk-update-items/`; encaminha o campo para o servico.
- `betor/services/bulk_update_items_service.py` -- `BulkUpdateItemsService.dispatch_maintenance_tasks`; deve combinar o filtro booleano com as consultas de itens recentes/elegiveis.
- `tests/betor/services/test_bulk_update_items_service.py` -- testes de contagem, limite e dispatch; deve cobrir `true`, `false` e ausencia do filtro.
- `tests/betor/services/test_list_items_service.py` -- arquivo a localizar/criar conforme a organizacao existente; deve verificar a composicao de filtros do servico.

## Tasks & Acceptance

**Execution:**
- [x] `betor/api/v1/items/router.py` e `betor/services/list_items_service.py` -- aceitar e propagar `Optional[bool]` e incluir a condicao MongoDB apenas quando definida -- habilitar filtragem no endpoint publico.
- [x] `betor/api/v1/admin/bulk_update_items_schemas.py`, `betor/api/v1/admin/router.py` e `betor/services/bulk_update_items_service.py` -- adicionar o campo opcional ao request e aplica-lo nas consultas de contagem e selecao -- habilitar filtragem no endpoint administrativo sem perder `false`.
- [x] `tests/betor/services/test_list_items_service.py` e `tests/betor/services/test_bulk_update_items_service.py` -- cobrir valores `true`, `false`, `None` e combinacao com filtros existentes -- impedir regressao na montagem das consultas.

**Acceptance Criteria:**
- Given `torrent_is_dying=true` ou `false` no GET `/v1/items/`, when a busca e executada, then somente itens com o valor booleano correspondente sao considerados.
- Given o query param do GET omitido, when a busca e executada, then o resultado mantem o comportamento anterior sem filtro por `torrent_is_dying`.
- Given `torrent_is_dying=true` ou `false` no POST `/v1/admin/bulk-update-items/`, when o processamento e iniciado, then as contagens e os itens enviados para tarefas usam o filtro combinado com a janela de atualizacao existente.
- Given `torrent_is_dying=None` no request administrativo, when o processamento e iniciado, then nenhuma consulta inclui esse campo e o comportamento anterior permanece.
- Given qualquer filtro existente combinado com `torrent_is_dying`, when a consulta e montada, then todas as condicoes sao preservadas simultaneamente.

## Verification

**Commands:**
- `poetry run pytest tests/betor/services/test_list_items_service.py tests/betor/services/test_bulk_update_items_service.py` -- expected: todos os testes de montagem de filtros e dispatch passam.
- `poetry run mypy betor/api/v1/items betor/api/v1/admin betor/services` -- expected: nenhuma nova incompatibilidade de tipos.

## Suggested Review Order

**Composicao das consultas**

- O servico administrativo reaproveita o filtro em contagens e selecao de itens.
	[`bulk_update_items_service.py:32`](../../betor/services/bulk_update_items_service.py#L32)

- O servico publico adiciona a condicao booleana sem alterar filtros existentes.
	[`list_items_service.py:56`](../../betor/services/list_items_service.py#L56)

**Contratos de entrada**

- O endpoint publico recebe e documenta o parametro booleano opcional.
	[`router.py:26`](../../betor/api/v1/items/router.py#L26)

- O payload administrativo declara o campo com ausencia preservando o comportamento anterior.
	[`bulk_update_items_schemas.py:15`](../../betor/api/v1/admin/bulk_update_items_schemas.py#L15)

- O router administrativo encaminha o valor ao servico de dispatch.
	[`router.py:90`](../../betor/api/v1/admin/router.py#L90)

**Verificacao**

- Os testes do servico publico cobrem `true`, `false` e `None`.
	[`test_list_items_service.py:17`](../../tests/betor/services/test_list_items_service.py#L17)

- Os testes administrativos cobrem combinacao com datas e ausencia de janela.
	[`test_bulk_update_items_service.py:201`](../../tests/betor/services/test_bulk_update_items_service.py#L201)
