---
id: SPEC-torrent-health-failure-window
companions:
  - ../../planning-artifacts/architecture/architecture-betor-2026-09-07/ARCHITECTURE-SPINE.md
sources:
  - ../../planning-artifacts/prds/prd-betor-2026-09-07/prd.md
---

> **Canonical contract.** Este SPEC e os arquivos listados em `companions:` formam o contrato completo, preservado e validado, para implementação e testes.

# Ajuste do Fluxo de Saúde de Torrent e Retenção de Falhas

## Why

Este trabalho existe para corrigir uma dor operacional no backend: o histórico de falhas de torrent cresce sem controle e os campos derivados de saúde podem ficar desatualizados quando não ocorre nova falha. Isso impacta a confiabilidade da triagem e das consultas que dependem de `torrent_failure_days`, `torrent_is_dying` e `torrent_is_dead`. O objetivo é garantir estado de saúde consistente e útil, com retenção de histórico limitada à janela relevante.

## Capabilities

- **CAP-1**
  - **intent:** O sistema recalcula o estado de saúde do torrent em toda execução do fluxo relevante, mesmo sem nova falha.
  - **success:** Após qualquer execução, `torrent_failure_days`, `torrent_is_dying` e `torrent_is_dead` refletem exatamente o histórico válido atual.

- **CAP-2**
  - **intent:** O sistema mantém `torrent_failure_history` apenas com ocorrências úteis dentro da janela temporal canônica.
  - **success:** Entradas com `occurred_at < now-7d` são removidas e entradas inválidas/futuras não impactam o cálculo.

- **CAP-3**
  - **intent:** O fluxo de atualização de saúde permanece determinístico e idempotente entre caminhos de sucesso e falha.
  - **success:** Duas execuções consecutivas sem novos eventos produzem o mesmo estado final; múltiplas falhas no mesmo dia contam como um único dia.

## Constraints

- Manter a arquitetura em camadas já existente, com cálculo de saúde centralizado no repository e tasks/services atuando como orquestradores.
- Atualização deve ocorrer de forma atômica por item, em um único pipeline de atualização.
- A regra temporal é canônica em UTC, com janela rolling de 7x24h.
- Não alterar os limiares de classificação existentes (`dying >= 1`, `dead >= 5`).
- Preservar os nomes e o contrato dos campos já expostos (`torrent_failure_history`, `torrent_failure_days`, `torrent_is_dying`, `torrent_is_dead`).
- A estratégia para base legada será de convergência natural pelas rotinas já existentes; não haverá backfill dedicado.

## Non-goals

- Redesenhar filas, pipelines ou a arquitetura geral além do fluxo específico de saúde de torrent.
- Introduzir novas telas de produto.
- Mudar semântica de classificação de dying/dead.
- Definir ou implantar métricas e alertas adicionais nesta fase.

## Success signal

Após implantação, uma execução completa das rotinas relevantes converte os itens para histórico enxuto e estado derivado consistente: o volume de entradas fora da janela deixa de crescer e reexecuções sem novos eventos não alteram o estado persistido.

