---
id: SPEC-bludv-gate-go-unlock
companions: []
---

# Desbloqueio de URLs Gate Go no Provedor Bludv

## Why

O provedor Bludv passou a utilizar o sistema de portões e redirecionamentos `gate/go/<token>?p=<id>` para proteger os links de download de torrent. O scraper atual não consegue extrair o link `magnet:` diretamente, resultando em perda de dados e falhas na catalogação. Precisamos de um mecanismo automatizado e performático (via Extension no Scrapy com suporte ao FlareSolverr e cache/reutilização de token) para destravar esses links de forma transparente.

## Capabilities

- **CAP-1**
  - **intent:** A extensão `UnlockBludvGateExtension` deve gerenciar a sessão do FlareSolverr de forma lazy (sob demanda na primeira solicitação) e garantir o fechamento no término do spider (`spider_closed`).
  - **success:** Sessão criada sob demanda e destruída corretamente ao fechar o spider.

- **CAP-2**
  - **intent:** A primeira solicitação de desbloqueio deve executar o fluxo completo de resolução (Jump page -> Parceiro -> Timer -> API End -> Go -> Callback) para adquirir um `token` mestre válido.
  - **success:** O token mestre é armazenado em cache na instância da extensão para uso subsequente.

- **CAP-3**
  - **intent:** As solicitações subsequentes de desbloqueio na mesma sessão devem utilizar o `token` mestre em cache com a mesma sessão do FlareSolverr para resolver diretamente via `/gate/callback?token={token}&ref={ref}`.
  - **success:** O magnet link é extraído instantaneamente sem repetir o fluxo de anúncios.

- **CAP-4**
  - **intent:** Caso ocorra qualquer falha utilizando o token em cache, a extensão deve realizar um mecanismo de fallback automático (destruir sessão, criar nova, reexecutar fluxo completo e atualizar o token).
  - **success:** Recuperação automática de erros sem falhar a execução do spider.

## Constraints

- O uso do FlareSolverr deve ser opcional ou tratado de forma segura com base nas configurações (`FLARESOLVERR_BASE_URL`).
- O spider do Bludv deve integrar a extensão para processar os links contendo `/gate/go/`.
- Cobertura de testes unitários abrangente para todas as camadas da extensão e helpers.

## Non-goals

- Alterar o comportamento de outros spiders além do Bludv.
- Modificar o armazenamento de dados no MongoDB além do modelo padrão do ProviderLoader.

## Success signal

1. O script de validação `scripts/test_bludv_gate_unlock.py` executa com sucesso e extrai o magnet link esperado.
2. Os testes unitários da extensão passam integralmente via `poetry run pytest`.
3. O spider do Bludv processa posts com links `gate/go` e popula `magnet_uris` corretamente.
