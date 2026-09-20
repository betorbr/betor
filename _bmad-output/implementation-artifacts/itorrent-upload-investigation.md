# Investigação: upload para iTorrent

## Contexto

O fluxo atual de metadata do torrent chama `UpdateItemTorrentInfoService.get_info_from_lt_session()`, que gera o arquivo `.torrent` localmente e, quando `itorrent_settings.upload_enabled` está ativo, chama `upload_to_itorrent()`.

O problema reportado foi: o upload "não rolou" e não foi possível acessar logs. O retorno Celery observável foi:

```json
{'torrent_name': 'Joe.Pickett.S02E05.1080p.WEB.h264-EDITH[TGx]', 'torrent_files': ['Joe.Pickett.S02E05.1080p.WEB.h264-EDITH.mkv', 'NEW upcoming releases by Xclusive.txt', '[TGx]Downloaded from torrentgalaxy.to .txt', 'joe.pickett.s02e05.1080p.web.h264-edith.nfo'], 'torrent_size': 4107634882, 'download_path': 'efb5b42ee97cdf256bbb9f3a189e244603a6cc2f.torrent', 'itorrent_uploaded_at': None}
```

Ou seja: o metadata foi extraído corretamente, o download local foi salvo, mas o campo `itorrent_uploaded_at` continuava `None`.

## Evidência reproduzida

Usando o arquivo `.torrent` presente na raiz do projeto, reproduzimos o POST real para o formulário público do iTorrent, no endpoint `https://itorrents.net/upload.php`.

### Teste real end-to-end do novo arquivo

Arquivo usado: `db617ae7e9d7b6c3c82be75df3071afbe75fd791.torrent`

- info hash esperado: `DB617AE7E9D7B6C3C82BE75DF3071AFBE75FD791` (nome do arquivo sem extensão)
- quando o arquivo ainda não existia no cache, os GETs para `http://itorrents.net/torrent/<hash>.torrent` falharam, como esperado
- após o upload, o HTML de sucesso retornou um link com o hash do arquivo
- a URL do torrent ficou disponível no cache do serviço
- o download em lowercase e uppercase foi aceito após o upload

Resultado concreto do teste de regressão válido:

```text
GET before upload -> http://itorrents.net/torrent/db617... -> HTTP 404
GET before upload -> http://itorrents.net/torrent/DB617... -> HTTP 404
POST upload -> HTTP 200
Resposta com link: /torrent/DB617AE7E9D7B6C3C82BE75DF3071AFBE75FD791.torrent
GET after upload -> http://itorrents.net/torrent/db617... -> HTTP 200
GET after upload -> http://itorrents.net/torrent/DB617... -> HTTP 200
```

Conclusão: o endpoint funcional é `/upload.php`, e o upload e o download real foram validados com sucesso.

## Código envolvido

- `betor/services/update_item_torrent_info_service.py`
- `betor/settings.py`
- `scripts/test_itorrent_upload.py`

## Causa raiz

A causa raiz do problema inicial era o endpoint errado: o código usava `autoupload.php`, mas a página pública do serviço aceita upload em `/upload.php`. O endpoint antigo retornava 200 com HTML de erro e nada que validasse como info hash; por isso o processo de upload caía em `None`.

A correção foi apontar a URL para o endpoint que realmente aceitou o arquivo em produção e deixar a validação defensiva do `info hash` no código para o caso do serviço responder algo inesperado.

## Artefato de isolamento e validação

A lógica de upload foi isolada em helpers reutilizáveis para permitir teste direto e diagnóstico sem rodar o Celery ou o fluxo inteiro.

### Funções extraídas

- `extract_itorrent_info_hash(response_text: str) -> str | None`
- `upload_torrent_to_itorrent(torrent_file_bytes: bytes, *, url: str, timeout: int = 10) -> tuple[bool, str | None, str]`

Essas funções permitem:

1. testar o endpoint real com um arquivo `.torrent`;
2. verificar o payload de resposta do serviço;
3. capturar logs de erro caso o serviço retorne algo inesperado.

## Script de teste recomendado

Executar este comando no projeto:

```bash
cd /Users/douglas.paz/dev/betor
source .venv/bin/activate
python scripts/test_itorrent_upload.py --torrent db617ae7e9d7b6c3c82be75df3071afbe75fd791.torrent
```

Esse script:

- testa `GET` antes do upload em lowercase e uppercase e espera falha;
- faz o POST para `https://itorrents.net/upload.php`;
- valida se o `info hash` retornado bate com o nome do arquivo;
- faz `GET` em lowercase e uppercase após o upload e espera sucesso.

## Prova do resultado

O teste foi executado no ambiente do projeto com o arquivo novo usando a URL correta do formulário e os retornos se comportaram conforme o esperado.

## Observações finais

- o endpoint correto do serviço é `/upload.php`;
- o endpoint antigo `autoupload.php` não deu resultado válido;
- o fluxo real do projeto já foi validado com upload e download do torrent em produção;
- os arquivos `.torrent` do projeto não devem ser commitados.
