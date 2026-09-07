---
title: Ajuste do Fluxo de Torrent Failure/Dying/Dead
status: final
created: 2026-09-07
updated: 2026-09-07
---

# PRD

## Resumo Executivo

- Ajustar o fluxo dos campos de saúde do torrent: torrent_failure_history, torrent_failure_days, torrent_is_dying e torrent_is_dead.
- O histórico de falhas está crescendo sem controle com dados antigos de baixo valor, enquanto os campos derivados podem ficar desatualizados quando não há falha nova.
- A rotina deve recalcular o estado de saúde em toda execução e manter apenas ocorrências válidas na janela rolling de 7x24h.

## Problema

- O campo torrent_failure_history cresce sem controle e mantém registros antigos sem utilidade operacional.
- Os campos derivados torrent_failure_days, torrent_is_dying e torrent_is_dead ficam desatualizados quando não ocorre nova falha, gerando estado inconsistente em relação ao histórico real.

## Objetivo

- Garantir que os campos de saúde do torrent representem sempre o estado real da janela móvel de 7 dias, mesmo quando não houver falha nova no ciclo atual.

## Escopo

- Ajustar as mesmas tasks/services já responsáveis por:
	- adicionar entradas em torrent_failure_history;
	- atualizar torrent_failure_days, torrent_is_dying e torrent_is_dead.
- Reutilizar a mesma rotina para também executar limpeza de histórico antigo.

## Não-Escopo

- Alterar limiares de classificação já existentes no sistema (dying >= 1 dia com falha e dead >= 5 dias com falha).
- Redesenhar pipelines, filas ou arquitetura de processamento além da rotina atual.
- Criar novas telas de produto; impactos de observabilidade ficam restritos a métricas e logs técnicos.

## Requisitos Funcionais

### FR-001 - Recalcular saúde sem dependência de nova falha

- As tasks/services já existentes devem recalcular torrent_failure_days, torrent_is_dying e torrent_is_dead mesmo quando não houver nova falha no momento da execução.
- O recálculo deve ocorrer em toda execução das rotinas atuais que processam saúde do torrent.
- O recálculo deve ser baseado exclusivamente nos dados válidos de torrent_failure_history dentro da janela de 7 dias.

### FR-002 - Limpeza automática de histórico antigo

- Na mesma rotina de atualização de saúde, remover entradas de torrent_failure_history cujo occurred_at seja menor que now-7d.
- Após a limpeza, os campos derivados devem refletir somente o histórico remanescente válido.

### FR-004 - Tratamento de bordas do histórico

- Entradas com occurred_at nulo, inválido ou não parseável devem ser descartadas do cálculo e registradas em log técnico.
- Entradas com occurred_at futuro não devem ser consideradas no cálculo de failure_days.
- Ausência de torrent_failure_history, valor nulo ou formato inválido deve ser tratada como histórico vazio.

### FR-005 - Idempotência da rotina

- Duas execuções consecutivas sem novos eventos de falha devem produzir o mesmo estado final (mesmo history válido e mesmos campos derivados).

### FR-006 - Regra de contagem por dias únicos

- torrent_failure_days deve representar a quantidade de dias distintos com falha na janela válida, e não a quantidade total de eventos.

### FR-003 - Consistência do estado derivado

- Sempre que a rotina executar, os campos torrent_failure_days, torrent_is_dying e torrent_is_dead devem sair consistentes com o conteúdo atual de torrent_failure_history após limpeza.

## Regras de Negócio

- Janela de análise: rolling window de 7x24h em UTC.
- Histórico expirado: qualquer ocorrência com occurred_at < now-7d deve ser removida.
- Estado de saúde deve ser recalculado a cada execução da rotina, independentemente da existência de nova falha.
- Classificação derivada: torrent_is_dying = true quando torrent_failure_days >= 1; torrent_is_dead = true quando torrent_failure_days >= 5.
- Se o histórico válido ficar vazio após limpeza, então torrent_failure_days = 0, torrent_is_dying = false e torrent_is_dead = false.

## Riscos e Mitigações

- Risco: concorrência entre execuções simultâneas atualizando o mesmo item.
Mitigação: manter atualização atômica por item no banco, com cálculo e persistência no mesmo fluxo de update.
- Risco: custo de processamento em itens com histórico inflado.
Mitigação: poda na mesma rotina para convergência natural do volume e redução de payload ao longo das execuções.
- Risco: divergência silenciosa de estado após deploy.
Mitigação: instrumentar logs e métricas de convergência (tamanho do history, itens com ajuste de days, proporção dying/dead).

## Critérios de Aceite

- Dado um item com falhas antigas (occurred_at < now-7d), quando a rotina executar, então essas falhas devem ser removidas de torrent_failure_history.
- Dado um item sem falha nova, quando a rotina executar, então torrent_failure_days, torrent_is_dying e torrent_is_dead devem ser atualizados com base no histórico válido.
- Dado um item com histórico válido dentro da janela, quando a rotina executar, então os campos derivados devem corresponder exatamente ao histórico considerado.
- Dado um item cujo histórico válido fique vazio após limpeza, quando a rotina executar, então o resultado deve ser torrent_failure_days = 0, torrent_is_dying = false e torrent_is_dead = false.
- Dado duas execuções consecutivas sem novos eventos, quando a rotina executar novamente, então o estado final deve permanecer inalterado (idempotência).
- Dado múltiplas falhas no mesmo dia, quando a rotina executar, então torrent_failure_days deve contar o dia apenas uma vez.
- Não deve haver crescimento indefinido de torrent_failure_history por retenção de dados fora da janela.
