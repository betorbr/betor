title: 'Rastreamento de saúde e falhas de torrents'
type: 'feature'
created: '2026-08-31'
status: 'done'
baseline_commit: '2eb1e6d7e1ae6d0df1938eb9dfbfcdb805825bc2'
review_loop_iteration: 0
context: []

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Torrents sem seeds podem falhar repetidamente: `update_item_torrent_info` termina por `SoftTimeLimitExceeded` e `update_item_torrent_trackers_info` não encontra resultado. Hoje essas falhas não ficam associadas ao `Item`, impedindo identificar torrents em deterioração ou já mortos.

**Approach:** Registrar cada falha por magnet URI com data e ponto de falha, calcular os dias distintos com falha na janela móvel de sete dias e derivar as flags de saúde. Substituir a asserção de trackers por exceção de domínio e adicionar timeout explícito à obtenção de metadados, mantendo as exceções propagadas após o registro.

## Boundaries & Constraints

**Always:** O histórico é uma única lista de registros `{occurred_at, failure_point}` e preserva cada tentativa. `failure_point` só pode ser `update_item_torrent_info` ou `update_item_torrent_trackers_info`. O contador considera cada data de calendário no intervalo inclusivo de hoje e dos seis dias anteriores, no máximo uma vez por dia. `torrent_is_dying` é verdadeiro quando o contador é `>= 1`; `torrent_is_dead` é verdadeiro quando é `>= 5`. Toda falha registrada atualiza `updated_at`, e a atualização alcança todos os itens com o `magnet_uri` informado.

**Ask First:** Nenhuma decisão adicional prevista; o timeout padrão deve permanecer configurável pela configuração existente do projeto.

**Never:** Não remover entradas do histórico, não contar tentativas repetidas do mesmo dia mais de uma vez, não transformar falha em sucesso silencioso, não manter `assert` para fluxo de negócio e não alterar a semântica dos updates bem-sucedidos.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Primeira falha | Item sem histórico; worker falha hoje | Adiciona um registro, contador `1`, `torrent_is_dying=True`, `torrent_is_dead=False`, atualiza `updated_at` | Repropaga a exceção original |
| Falhas repetidas no mesmo dia | Histórico recebe duas tentativas hoje | Mantém os dois registros, mas o contador aumenta somente uma vez | Repropaga cada falha |
| Janela móvel | Histórico contém datas anteriores a seis dias atrás e datas dentro da janela | Ignora datas fora da janela e conta apenas dias distintos dentro dela | Nenhuma |
| Sem resultado de tracker | Scraper não retorna dados | `get_torrent_trackers_info` lança exceção customizada | Worker registra o ponto de falha e repropaga |
| Metadados sem resposta | `has_metadata()` permanece falso até o timeout configurado | `get_info_from_lt_session` lança exceção customizada | Worker registra o ponto de falha e repropaga |

</frozen-after-approval>

## Code Map

- `betor/entities/item.py`, `torrent_info.py` e `torrent_trackers_info.py` -- contratos TypedDict; incluir o histórico e os três campos de saúde no contrato de `Item`.
- `betor/repositories/items_repository.py` -- `parse_result`, `build_data` e updates por `magnet_uri`; adicionar persistência atômica do registro, contador, flags e `updated_at`, sem incluir campos derivados no hash de conteúdo.
- `betor/services/update_item_torrent_info_service.py` -- `get_info_from_lt_session`; substituir espera indefinida por timeout configurável e exceção customizada.
- `betor/services/update_item_torrent_trackers_info_service.py` -- `get_torrent_trackers_info`; substituir `assert result` por exceção customizada.
- `betor/celery/tasks.py` -- `_update_item_torrent_info` e `_update_item_torrent_trackers_info`; capturar falhas conhecidas, registrar por `magnet_uri`, fechar o cliente e repropagar a exceção.
- `betor/exceptions.py` e `betor/settings.py` -- exceções de domínio e configuração do timeout.
- `tests/betor/repositories/test_items_repository.py` e novos testes em `tests/betor/services/` -- verificar cálculo de dias distintos, flags, atualização de data, timeout, exceção de tracker e repropagação/registro dos workers.

## Tasks & Acceptance

**Execution:**
- [x] `betor/entities/*.py` -- modelar o registro de falha e os campos de saúde no `Item` -- manter o contrato tipado compatível com documentos antigos sem esses campos.
- [x] `betor/exceptions.py` e `betor/settings.py` -- criar exceções específicas e timeout configurável com padrão de 5 minutos -- remover fluxo baseado em `assert` e espera indefinida.
- [x] `betor/repositories/items_repository.py` -- persistir cada falha e recalcular a saúde na janela de sete dias por `magnet_uri` -- garantir histórico completo, deduplicação somente no contador e `updated_at` por tentativa.
- [x] `betor/services/update_item_torrent_info_service.py`, `betor/services/update_item_torrent_trackers_info_service.py` e `betor/celery/tasks.py` -- integrar timeout, exceção de trackers, registro e repropagação -- cobrir ambos os pontos de falha.
- [x] `tests/betor/repositories/test_items_repository.py` e `tests/betor/services/` -- testar matriz de casos e contratos dos workers -- validar comportamento sem depender de serviços externos.

**Acceptance Criteria:**
- Given uma falha de qualquer worker para um magnet URI, when ela é tratada, then todos os itens desse magnet recebem um novo registro com data, ponto correto, saúde recalculada e `updated_at` atualizado.
- Given cinco ou mais dias distintos com falha nos últimos sete dias, when a saúde é recalculada, then `torrent_is_dead` é verdadeiro; com pelo menos um dia, `torrent_is_dying` é verdadeiro.
- Given repetição de falhas no mesmo dia, when os registros são persistidos, then todas as tentativas permanecem no histórico e o contador representa um único dia.
- Given ausência de resultado dos trackers ou timeout de metadados, when o worker termina, then uma exceção customizada é registrada e a falha original continua disponível ao Celery.

## Design Notes

O cálculo deve usar as datas dos registros persistidos e ser seguro para tentativas concorrentes do mesmo magnet URI: o append e a atualização dos campos derivados não podem descartar histórico já gravado. Documentos legados devem ser tratados como histórico vazio e flags ausentes equivalentes a `False`.

## Verification

**Commands:**
- `poetry run pytest tests/betor/repositories/test_items_repository.py tests/betor/services` -- expected: SUCCESS; testes da persistência, serviços e matriz de falhas passam.
- `poetry run flake8 betor tests/betor/repositories/test_items_repository.py tests/betor/services` -- expected: SUCCESS.
- `poetry run mypy betor` -- expected: SUCCESS.

## Suggested Review Order

**Registro nos workers**

- Preserva a exceção original enquanto tenta registrar a falha.
	[`tasks.py:64`](../../betor/celery/tasks.py#L64)

- Atribui o ponto correto ao histórico de falhas dos trackers.
	[`tasks.py:121`](../../betor/celery/tasks.py#L121)

**Cálculo da saúde**

- Faz append atômico e calcula dias distintos incluindo a tentativa atual.
	[`items_repository.py:298`](../../betor/repositories/items_repository.py#L298)

- Define as flags pelos limiares aprovados e atualiza `updated_at`.
	[`items_repository.py:345`](../../betor/repositories/items_repository.py#L345)

**Exceções e timeout**

- Impõe limite configurável à espera de metadados do libtorrent.
	[`update_item_torrent_info_service.py:30`](../../betor/services/update_item_torrent_info_service.py#L30)

- Usa exceção de domínio para ausência de resultado dos trackers.
	[`update_item_torrent_trackers_info_service.py:47`](../../betor/services/update_item_torrent_trackers_info_service.py#L47)

**Contratos e testes**

- Mantém defaults para documentos legados e tipa o histórico de falhas.
	[`item.py:28`](../../betor/entities/item.py#L28)

- Verifica o pipeline de persistência e defaults de leitura.
	[`test_items_repository.py:208`](../../tests/betor/repositories/test_items_repository.py#L208)

- Exercita as exceções específicas nos serviços.
	[`test_update_item_torrent_services.py:8`](../../tests/betor/services/test_update_item_torrent_services.py#L8)
