# Product Requirements Document (PRD): Desbloqueio de URLs Gate Go no Bludv

## 1. Visão Geral e Contexto

O provedor **Bludv** (`bludvfilmes2.xyz`) atualizou seus links de download de torrent, substituindo o redirecionador antigo (SystemAds) por um novo sistema interno de portões e redirecionamentos estruturado em rotas do tipo `/gate/go/<token>?p=<id>`.

Atualmente, o Scrapy Spider do Bludv extrai URLs de gate que bloqueiam a extração direta do link `magnet:`. O objetivo desta iniciativa é implementar o mecanismo de desbloqueio automatizado dessas URLs no `BludvSpider`, permitindo a extração bem-sucedida de metadados e magnet links para alimentar o ecossistema P2P do BeTor.

## 2. Objetivos e Critérios de Sucesso

- **Objetivo Principal:** Destravar automaticamente links do tipo `/gate/go/` do Bludv durante a raspagem para obter o link `magnet:` correto.
- **Resiliência a Cloudflare:** Utilizar a integração com FlareSolverr (`https://flaresolverr.betor.top`) para superar os desafios de proteção Cloudflare Turnstile/challenge presentes no provedor e no hub de redirecionamento.
- **Otimização de Desempenho (Token Reuse):** Aproveitar a descoberta de que um único token mestre de sessão do FlareSolverr pode ser reutilizado para destravar múltiplos links de gate (`ref`), evitando a repetição desnecessária de saltos e timers para cada item do catálogo.
- **Testabilidade:** Manter 100% de cobertura de testes unitários sem dependências externas reais.

## 3. Fluxo Funcional Mapeado (User/Bot Journey)

1. **Entrada:** O spider encontra o link `https://bludvfilmes2.xyz/gate/go/<token>?p=<id>`.
2. **Salto (*Jump*):** O request inicial retorna HTTP `307` apontando para o hub `promobr.online/jump/...`.
3. **Parceiro & Código (`utm_content`):** A página de salto expõe um link de parceiro (`valedesconto.shop/r/...`) contendo o código criptografado em `utm_content`.
4. **Engajamento & Sessão:** O spider visita a página do parceiro mantendo a mesma sessão do FlareSolverr para estabelecer cookies e rastreamento.
5. **API End & Go:** Chamadas sequenciais a `https://promobr.online/api/end?code=<code&>` e `https://promobr.online/go/<code>` liberam o redirecionamento para o callback do Bludv: `/gate/callback?token=<token>&ref=<ref>`.
6. **Extração Final:** A página de callback exibe o link `magnet:` injetado em uma variável JavaScript (`var u="magnet:?..."`), que é extraído via expressão regular.

## 4. Requisitos Não-Funcionais

- **Conformidade com a Arquitetura BeTor:** Seguir os padrões estabelecidos de loaders, spiders e utilitários em Scrapy.
- **Tratamento de Exceções Defensivo:** Caso um link de gate falhe ou mude de estrutura, o spider deve registrar um log de aviso/depuração sem interromper a execução do lote de outros itens.
- **Isolamento de Testes:** Prover testes unitários com mocks robustos para garantir regressão zero.
