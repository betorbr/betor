# Checklist Tecnico - Ajustes Arquiteturais iTorrent

## Objetivo
Consolidar as alteracoes incrementais apos a primeira implementacao da integracao iTorrent: settings dedicados, util compartilhada de info hash e revisao de compatibilidade no contrato Item.

## 1. Settings dedicados do iTorrent
Arquivo alvo: betor/settings.py

- [ ] Criar classe ITorrentSettings com env_prefix proprio (`itorrent_`).
- [ ] Incluir flags dedicadas:
- [ ] `upload_enabled` (padrao true)
- [ ] `download_enabled` (padrao true)
- [ ] Incluir configuracoes de endpoint/base URL do iTorrent:
- [ ] `autoupload_url`
- [ ] `public_download_base_url`
- [ ] Instanciar `itorrent_settings` junto dos demais settings globais.
- [ ] Remover flags de iTorrent que nao pertencem a StoreTorrentFileSettings.

Criterios de pronto:
- [ ] Configuracao de iTorrent totalmente isolada de configuracao de storage generico de arquivos `.torrent`.

## 2. Util compartilhada de info hash
Arquivo alvo: betor/utils.py

- [ ] Criar funcao `extract_magnet_info_hash(magnet_uri: str) -> Optional[str]`.
- [ ] Parsear magnet com `torf.Magnet.from_string`.
- [ ] Manter fallback para casos base32, retornando hash em hexadecimal quando valido.
- [ ] Retornar None em magnet invalido ou hash inconsistente.

Criterios de pronto:
- [ ] A funcao cobre hash hex direto, fallback base32 e entrada invalida.

## 3. Reuso da util no schema de API
Arquivo alvo: betor/api/v1/items/schemas.py

- [ ] Remover parsing local/duplicado de info hash no schema.
- [ ] Usar `extract_magnet_info_hash` na geracao de `download_url` iTorrent.
- [ ] Usar `itorrent_settings.download_enabled` para habilitacao de download.
- [ ] Manter fallback para comportamento atual com `store_torrent_file_settings.public_download_base_url`.

Criterios de pronto:
- [ ] Sem regressao no fallback quando `itorrent_uploaded_at` for nulo.

## 4. Reuso da util no servico de trackers
Arquivo alvo: betor/services/update_item_torrent_trackers_info_service.py

- [ ] Substituir normalizacao manual do infohash pela util compartilhada.
- [ ] Preservar comportamento atual de busca por trackers.

Criterios de pronto:
- [ ] Nao ha duplicacao de logica de parsing de magnet/info hash.

## 5. Revisao da construcao de Item
Arquivos alvo:
- betor/services/process_raw_item_service.py
- tests/conftest.py
- betor/repositories/items_repository.py

- [ ] Garantir que o campo `itorrent_uploaded_at` esteja contemplado nos pontos principais de construcao/parse.
- [ ] Revisar campos excluidos do hash do item para evitar mudanca indevida de comportamento.
- [ ] Garantir compatibilidade com documentos legados sem o novo campo.

Criterios de pronto:
- [ ] Campo novo nao quebra fluxo de item novo nem item legado.

## 6. Testes
Arquivos alvo:
- tests/betor/services/test_update_item_torrent_services.py
- tests/betor/api/v1/items/test_schemas.py
- tests/betor/test_utils.py

- [ ] Atualizar testes para `itorrent_settings`.
- [ ] Cobrir util `extract_magnet_info_hash` (hex, base32, invalido).
- [ ] Validar fallback do `download_url` com e sem iTorrent ativo.

Criterios de pronto:
- [ ] Testes impactados passam sem mocks complexos de bibliotecas externas.

## 7. Validacao final
- [ ] Executar bateria de testes impactados.
- [ ] Conferir PRD atualizado com nova decisao arquitetural.
- [ ] Registrar alteracoes no memlog do run.
