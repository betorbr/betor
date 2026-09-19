# DarkMahou

## Arquitetura

O provider `darkmahou` participa de `PROVIDERS` e `ProviderSlug`.
A coleta e a busca usam o mesmo contrato `deep` / `q` dos outros spiders:

1. `https://darkmahou.io/feed/`, com `paged` para paginação e `s` para busca.
2. Cada `rss/channel/item/link` leva à página do post (não ao GUID antigo).
3. O spider lê os downloads de `.soraddl`: magnets diretos e
   `redirect.php?url=<base64>`, incluindo Base64 URL-safe e sem padding.
4. Valida com `torf.Magnet`, elimina hashes repetidos no post e entrega um
   `ScrapyItem` com todos os releases válidos ao `ProviderLoader`.
5. `RawItemsPipeline` → `ProcessRawItemService` → tarefas Celery existentes.
   Cada magnet mantém seu `dn`, hash e trackers; episódios e batches com
   hashes diferentes continuam separados.

Não são necessários novos endpoints, migrações, dependências ou alterações
nos serviços de processamento. O provider usa uma subclasse pequena para que
a primeira página seja o feed sem alterar o comportamento dos demais providers.
O spider não acessa o encurtador nem os destinos decodificados.

## Verificação da fonte

Em 19/09/2026 foram consultados o feed, sua segunda página, a busca
`/feed/?s=solo`, o robots.txt e páginas de posts. O RSS continha sinopses,
sem os downloads. A página de Solo Leveling S02 continha magnets diretamente
no HTML e JavaScript que os transforma em redirects Base64 no navegador.
Por isso a integração lê as páginas e suporta os dois formatos sem JavaScript.
O robots.txt consultado restringia caminhos administrativos/REST, não o feed
ou os posts. Permanecem os limites de concorrência e espera existentes.

## Catálogo e Prowlarr

O `betor-catalog` em main já importa os itens do BeTor sem uma lista de
providers permitidos. Preserva `provider_slug`, `provider_url`,
`magnet_uri` e `magnet_dn` na geração do catálogo e da busca.
Nenhuma mudança nesse repositório é necessária.

Depois de atualizar BeTor API, Scrapyd e workers com esta branch:
- Dispare `GET /v1/search/?q=solo&provider=darkmahou&deep=1` na API
  configurada e acompanhe o job retornado.
- Confira os raw items e os itens processados nos endpoints documentados
  em `/docs`. Um post deve gerar um raw item com vários magnets e depois
  um item por hash válido, quando a identificação da obra tiver sucesso.
- No ambiente já configurado do catálogo, execute
  `betor-catalog data-fetch-items`, `betor-catalog data-catalog-items` e
  `betor-catalog build`, e publique pelo fluxo habitual.
- Use a definição existente `src/static/catalogo-betor.yml` do catálogo
  no Prowlarr, ou a definição `prowlarr-betor.yml` para o BeTor.
  A integração continua Cardigann; não foi adicionada uma API Torznab.

## Testes

Sem serviços externos:

```sh
poetry run pytest tests/betor_scrapy/spiders/test_darkmahou.py
poetry run pytest tests
poetry run flake8 betor betor_scrapy tests acceptance_tests
poetry run mypy betor betor_scrapy tests acceptance_tests
```

Os testes usam conteúdo sintético com a estrutura observada na fonte:
paginação/busca, RSS sem downloads, links duplicados/externos, formatos
Base64, payloads inválidos, ano de lançamento, fallback de título,
múltiplos releases e preservação do contrato RawItem.
A CI existente executa os testes no PR.

Com MongoDB, Redis, Scrapyd e workers configurados, a coleta também pode
ser executada com `poetry run scrapy crawl darkmahou -a deep=1 -a q=solo`.
Esse comando usa os pipelines normais e grava/processa dados.

## Limitações

- RSS é uma janela paginada de posts, não uma garantia de cobertura histórica
  completa nem um registro confiável de alterações em downloads de posts antigos.
  `deep` limita as páginas consultadas; posts de páginas diferentes são
  deduplicados pelo mecanismo normal de requests do Scrapy.
- Links HTTP de arquivos, Nyaa, serviços de hospedagem e redirects para
  destinos não-magnet são ignorados. Posts sem magnets suportados não são emitidos.
- A identificação IMDb/TMDB mantém as estratégias existentes. Títulos japoneses,
  temporadas com nomes próprios e OVAs podem precisar do mapeamento de URL
  para IMDb já oferecido pelo BeTor.
- O catálogo mantém seus filtros: a importação exige IMDb, tipo, magnet e tamanho;
  a geração do catálogo exige também TMDB e data de atualização. Um raw item
  coletado não garante sua exibição antes do enriquecimento.
- Idiomas, temporadas e episódios continuam sendo extraídos pelos serviços
  existentes, sem assumir que uma legenda PT-BR significa áudio PT-BR.
  Nomes com numeração absoluta ou "Season 2" podem não ser reconhecidos pelos
  padrões atuais de episódios/temporadas. Não são inventados seeds, tamanhos
  ou metadados ausentes.
- O teste completo Prowlarr → Sonarr → cliente torrent depende do ambiente do
  operador e não é coberto pelos testes unitários.
