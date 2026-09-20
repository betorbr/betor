---
title: 'Recalcular e Podar Saúde de Torrent em Rotinas Existentes'
type: 'bugfix'
created: '2026-09-07'
status: 'done'
review_loop_iteration: 1
baseline_commit: '2fd91abdda991cfd22cdfe404168d10c3b9d16b9'
context:
  - '{project-root}/_bmad-output/specs/spec-torrent-health-failure-window/SPEC.md'
  - '{project-root}/_bmad-output/planning-artifacts/architecture/architecture-betor-2026-09-07/ARCHITECTURE-SPINE.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Os campos de saúde de torrent (torrent_failure_days, torrent_is_dying, torrent_is_dead) ficam desatualizados quando não ocorre nova falha, e o torrent_failure_history cresce com registros antigos sem valor.

**Approach:** Reutilizar e centralizar a lógica de cálculo no repository para rodar também sem falha nova, com poda de histórico fora da janela canônica e manutenção de idempotência, conectando essa rotina aos fluxos já existentes de atualização.

## Boundaries & Constraints

**Always:** Preservar contrato dos campos existentes; manter cálculo no repository; executar atualização atômica por item em pipeline MongoDB; usar janela temporal canônica em UTC; manter limiares atuais (dying >= 1, dead >= 5); contar dias únicos com falha.

**Ask First:** Alterar semântica de janela temporal; mudar limiares de dying/dead; introduzir backfill dedicado; adicionar métricas/alertas nesta entrega; alterar payloads da API.

**Never:** Redesenhar arquitetura geral, filas ou pipelines além deste fluxo; criar tela nova; duplicar lógica de cálculo em tasks/services; quebrar compatibilidade de schemas.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Recalculo sem nova falha | Item com history válido e execução normal de rotina de atualização | days/dying/dead recalculados com base no history atual, sem necessidade de novo evento | N/A |
| Poda de histórico expirado | history contendo ocorrências com occurred_at menor que now-7d | ocorrências expiradas removidas de torrent_failure_history e derivados recalculados | N/A |
| Histórico vazio ou ausente | history nulo, ausente ou vazio | resultado convergente: days=0, dying=false, dead=false | tratar como vazio |
| Múltiplas falhas no mesmo dia | vários eventos no mesmo dia calendário | failure_days conta 1 dia para aquele calendário | N/A |
| Timestamp inválido/futuro | entrada com occurred_at inválido ou em data futura | entrada não influencia cálculo e não gera estado incorreto | descartar do cálculo e registrar log técnico |
| Duas execuções consecutivas sem novos eventos | mesmo estado de entrada em duas execuções seguidas | estado final idêntico após segunda execução | N/A |

</frozen-after-approval>

## Code Map

- betor/repositories/items_repository.py -- núcleo do cálculo atual em record_torrent_failure (aprox. 298-356); extrair helper de pipeline e adicionar método público de recálculo sem append.
- betor/celery/tasks.py -- paths de falha já chamam record_torrent_failure (aprox. 62-85 e 119-140); incluir disparo da rotina de recálculo no ciclo normal relevante.
- betor/services/update_item_torrent_info_service.py -- fluxo de sucesso de metadata; ponto de integração para garantir recálculo no caminho sem exception.
- betor/services/update_item_torrent_trackers_info_service.py -- fluxo de sucesso de trackers; mesmo ponto de integração para recálculo consistente.
- betor/services/admin_bulk_update_item_service.py -- rotina que dispara atualizações dos itens; possível ponto para garantir execução da manutenção de saúde no ciclo operacional.
- betor/celery/app.py -- mapa de roteamento de filas; incluir rota de eventual task dedicada de recálculo se adotada.
- tests/betor/repositories/test_items_repository.py -- já valida shape básico do pipeline; expandir para poda, idempotência, dias únicos, sem nova falha e bordas temporais.
- tests/betor/celery/test_torrent_failure_tasks.py -- já valida path de exceção; expandir para validar path sem falha e fechamento de conexão.
- betor/entities/item.py -- contrato de tipo dos campos de saúde (linhas de definição dos 4 campos); somente referência de compatibilidade.
- betor/api/v1/items/schemas.py -- contrato exposto na API dos campos de saúde; garantir ausência de breaking change.

## Tasks & Acceptance

**Execution:**
- [x] betor/repositories/items_repository.py -- extrair builder canônico de pipeline de saúde e criar método reutilizável para recálculo sem falha nova, incluindo poda por janela temporal -- evita duplicação e drift entre paths.
- [x] betor/repositories/items_repository.py -- adaptar record_torrent_failure para reaproveitar o mesmo builder canônico (com append de falha) -- garante uma única fonte de verdade para cálculo.
- [x] betor/services/update_item_torrent_info_service.py -- acionar rotina de manutenção de saúde após update bem-sucedido do torrent info -- corrige defasagem quando não há exception.
- [x] betor/services/update_item_torrent_trackers_info_service.py -- acionar rotina de manutenção de saúde após update bem-sucedido de trackers -- mantém consistência no segundo fluxo operacional.
- [x] betor/celery/tasks.py -- preservar path de registro de falha e garantir que o ciclo normal também dispare o recálculo de saúde (direto via service existente ou task dedicada roteada em torrents) -- cobre ambos os caminhos operacionais.
- [x] betor/celery/app.py -- atualizar task_routes apenas se for criada task dedicada para recálculo -- mantém roteamento explícito e previsível.
- [x] tests/betor/repositories/test_items_repository.py -- adicionar testes para recálculo sem nova falha, poda de expirados, histórico vazio/ausente, dias únicos, idempotência e bordas temporais -- protege regras de negócio do SPEC.
- [x] tests/betor/celery/test_torrent_failure_tasks.py -- adicionar testes para path sem falha e garantia de fechamento de conexão em sucesso/erro -- protege comportamento operacional das tasks.

**Acceptance Criteria:**
- Given item com histórico contendo eventos válidos e expirados, when a rotina de manutenção de saúde executar, then o history persiste apenas eventos na janela canônica e os campos derivados refletem somente os eventos remanescentes.
- Given item sem nova falha durante uma execução de atualização normal, when o fluxo completar, then torrent_failure_days, torrent_is_dying e torrent_is_dead são recalculados a partir do history atual.
- Given item com múltiplos eventos no mesmo dia calendário, when o recálculo executar, then torrent_failure_days contabiliza aquele dia apenas uma vez.
- Given history ausente, nulo ou vazio, when o recálculo executar, then o estado final é days=0, dying=false e dead=false.
- Given duas execuções consecutivas sem novos eventos, when a segunda execução terminar, then o estado derivado permanece idêntico ao final da primeira.
- Given contratos atuais de entidade e schema, when a mudança for aplicada, then nomes/tipos dos campos de saúde permanecem inalterados e sem breaking change na API.

## Spec Change Log

- Iteração 1 (step-04): achado patch aplicado para evitar deriva temporal por datetime naive/local no path de falha das tasks Celery. Alteração: `occurred_at` passou a ser gerado com `datetime.now(UTC)` em `betor/celery/tasks.py`, com reforço de testes em `tests/betor/celery/test_torrent_failure_tasks.py` para garantir payload timezone-aware UTC. Estado ruim evitado: descarte incorreto de eventos válidos como "future" por comparação entre relógios/offsets implícitos.

## Design Notes

A decisão estrutural é manter uma única fonte de cálculo no repository para todos os caminhos. O fluxo de sucesso e o fluxo de exceção devem convergir para a mesma regra canônica, evitando inconsistência temporal e duplicação de lógica.

A janela temporal deve continuar canônica e previsível para testes: comparar datas em UTC e derivar failure_days por dias distintos, não por contagem bruta de eventos.

## Verification

**Commands:**
- poetry run pytest tests/betor/repositories/test_items_repository.py -- expected: novos cenários de saúde/poda/idempotência passando.
- poetry run pytest tests/betor/celery/test_torrent_failure_tasks.py -- expected: paths de falha e sem falha validados com fechamento de conexão.
- poetry run pytest tests/betor/services/test_admin_bulk_update_item_service.py -- expected: fluxo de despacho segue íntegro se houver integração adicional.
- poetry run mypy . -- expected: sem erros de tipagem novos.
- poetry run flake8 -- expected: sem violações de lint novas.

## Suggested Review Order

**Núcleo de Consistência de Saúde**

- Concentra cálculo, poda e derivação em pipeline único e atômico no repository.
  [items_repository.py:312](../../betor/repositories/items_repository.py#L312)

- Expõe rotina canônica sem append para recálculo em ciclos sem falha.
  [items_repository.py:375](../../betor/repositories/items_repository.py#L375)

- Reusa o mesmo pipeline no path de falha para evitar drift lógico.
  [items_repository.py:382](../../betor/repositories/items_repository.py#L382)

**Convergência dos Fluxos Operacionais**

- Garante UTC explícito ao registrar falha no caminho de timeout.
  [tasks.py:73](../../betor/celery/tasks.py#L73)

- Garante UTC explícito ao registrar falha no caminho de trackers.
  [tasks.py:130](../../betor/celery/tasks.py#L130)

- Aciona manutenção após sucesso de metadata para recálculo sem exceção.
  [update_item_torrent_info_service.py:22](../../betor/services/update_item_torrent_info_service.py#L22)

- Aciona manutenção após sucesso de trackers no ciclo normal.
  [update_item_torrent_trackers_info_service.py:23](../../betor/services/update_item_torrent_trackers_info_service.py#L23)

**Verificação e Regressão**

- Cobre recálculo, janela rolling, idempotência e bordas de timestamp no repository.
  [test_items_repository.py:212](../../tests/betor/repositories/test_items_repository.py#L212)

- Cobre payload UTC-aware no registro de falha nas tasks Celery.
  [test_torrent_failure_tasks.py:27](../../tests/betor/celery/test_torrent_failure_tasks.py#L27)

- Cobre gatilho de manutenção nos caminhos de sucesso dos services.
  [test_update_item_torrent_services.py:16](../../tests/betor/services/test_update_item_torrent_services.py#L16)
