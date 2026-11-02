# Investigação e Validação: Desbloqueio de URLs Gate Go no Bludv (`gate/go`)

## Contexto

As páginas do provedor **Bludv** utilizam o sistema de proteção e redirecionamento intermediário `gate/go/<token>?p=<id>`. Através da análise de arquivos `.har` e validação com scripts em Python utilizando o FlareSolverr (`https://flaresolverr.betor.top`), mapeamos e validamos com sucesso o fluxo completo de ponta a ponta.

---

## Descoberta Crítica: Reutilização de Token na Mesma Sessão

Testamos se o `token` gerado após concluir o fluxo de um link de gate pode ser reutilizado para destravar outros links de gate (`ref` diferentes) dentro da **mesma sessão do FlareSolverr**.

### Resultado do Teste
- **Comprovado com Sucesso!** Quando mantida a mesma sessão do FlareSolverr, um único fluxo completo executado em uma URL de gate gera um `token` válido que **consegue destravar qualquer outra URL de gate** apenas chamando diretamente:
  `https://bludvfilmes2.xyz/gate/callback?token={token}&ref={ref}`

### Vantagem Arquitetural para o Spider
1. **Otimização de Desempenho:** O spider não precisa passar pelo fluxo pesado de salto (*jump*), visita ao parceiro (`valedesconto.shop`) e timer de engajamento para **cada** item/filme.
2. **Estratégia de Execução:** 
   - Ao iniciar a varredura do Bludv (ou quando necessário), o spider resolve a primeira URL de gate do lote para obter o `token` válido na sessão.
   - Para os demais itens do mesmo lote, o spider pode realizar requisições diretas ao `/gate/callback` utilizando esse `token` e o respectivo `ref` extraído da URL `/gate/go/<ref>?p=...`.

---

## Script de Validação Standalone Atualizado
- `scripts/test_bludv_gate_unlock.py`
