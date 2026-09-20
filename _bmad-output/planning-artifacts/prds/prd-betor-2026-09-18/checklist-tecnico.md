# Checklist Tecnico - Integracao iTorrent

## 1. Preparacao
- [ ] Confirmar branch de feature dedicada para implementacao.
- [ ] Validar variaveis de ambiente esperadas para StoreTorrentFileSettings.
- [ ] Definir nome das chaves de ambiente para flags de upload e download iTorrent.

## 2. Configuracao (FR-1, FR-2)
Arquivo alvo: betor/settings.py

- [ ] Adicionar flag booleana de upload iTorrent com padrao true em StoreTorrentFileSettings.
- [ ] Adicionar flag booleana de download iTorrent com padrao true em StoreTorrentFileSettings.
- [ ] Manter propriedade enabled existente sem regressao funcional.
- [ ] Garantir coerencia de nomes entre atributos, env prefix e uso em servicos/schemas.

Criterios de pronto:
- [ ] Com env ausente, ambas as flags ficam true.
- [ ] Com env false, comportamento e desativado sem efeitos colaterais.

## 3. Contrato de Dominio (FR-3)
Arquivo alvo: betor/entities/torrent_info.py

- [ ] Adicionar campo opcional de data de upload no iTorrent ao TypedDict TorrentInfo.
- [ ] Usar datetime nativo da aplicacao como tipo do campo (padrao atual do projeto).

Criterios de pronto:
- [ ] Campo aceita valor datetime e None.
- [ ] Nao quebra tipagem dos consumidores atuais de TorrentInfo.

## 4. Upload para iTorrent no servico (FR-5)
Arquivo alvo: betor/services/update_item_torrent_info_service.py

- [ ] Implementar fluxo condicional de upload para iTorrent dentro de get_info_from_lt_session.
- [ ] Acionar upload somente quando flag upload_to_itorrent estiver true.
- [ ] Gerar payload .torrent e enviar para endpoint de automacao do iTorrent.
- [ ] Em sucesso, preencher data de upload no TorrentInfo.
- [ ] Em falha, seguir fail-open: nao interromper processamento e manter data de upload nula quando sem valor anterior.
- [ ] Preservar fluxo atual de timeout/metadados do libtorrent.
- [ ] Adicionar log de observabilidade para sucesso/falha de upload iTorrent.

Criterios de pronto:
- [ ] Sem regressao no retorno de torrent_name, torrent_files, torrent_size e download_path.
- [ ] Falha de upload nao impede update_torrent_info no repositorio.
- [ ] Campo de data de upload reflete sucesso real do envio.

## 5. Regra de download_url no schema (FR-4)
Arquivo alvo: betor/api/v1/items/schemas.py

- [ ] Ajustar computed_field download_url para suportar regra iTorrent quando download via iTorrent estiver ativo.
- [ ] Formar URL como http://itorrents.net/torrent/<INFO_HASH>.torrent com hash em maiusculo.
- [ ] Se download via iTorrent ativo e data de upload ausente/nula, manter comportamento atual:
- [ ] usar public_download_base_url quando configurado e houver download_path.
- [ ] retornar None quando base URL/caminho nao estiverem disponiveis.
- [ ] Se download via iTorrent desativado, manter comportamento atual integralmente.

Criterios de pronto:
- [ ] URLs iTorrent apenas quando condicoes de uso forem satisfeitas.
- [ ] Fallback atual preservado sem quebra para clientes existentes.

## 6. Persistencia e compatibilidade
Arquivos alvo: betor/repositories/items_repository.py e consumidores de ItemSchema

- [ ] Garantir que update_torrent_info persiste novo campo datetime junto aos demais dados de torrent.
- [ ] Verificar parse_result para refletir o novo campo sem perdas de tipo.
- [ ] Verificar compatibilidade com documentos antigos sem campo de data (valor None).

Criterios de pronto:
- [ ] Itens legados continuam validando e sendo serializados.
- [ ] Novo campo nao impacta hash/campos excluidos sem decisao explicita.

## 7. Testes unitarios e de contrato
Arquivos alvo sugeridos:
- tests/betor/services/test_update_item_torrent_info_service.py
- tests/betor/api/v1/items/test_schemas.py (ou modulo equivalente)
- tests/betor/repositories/test_items_repository.py

- [ ] Teste: flags default true em StoreTorrentFileSettings.
- [ ] Teste: upload iTorrent chamado quando flag upload true.
- [ ] Teste: upload iTorrent nao chamado quando flag upload false.
- [ ] Teste: falha de upload nao interrompe fluxo e data permanece None.
- [ ] Teste: sucesso de upload preenche data de upload com datetime.
- [ ] Teste: download_url gera URL iTorrent com info hash uppercase quando habilitado.
- [ ] Teste: download_url faz fallback para comportamento atual quando data de upload e None.
- [ ] Teste: download_url com iTorrent desabilitado mantem comportamento atual.

Criterios de pronto:
- [ ] Suite relevante passando com poetry run pytest tests.

## 8. Validacao manual rapida
- [ ] Subir ambiente local e processar um magnet de teste.
- [ ] Confirmar no documento do item persistido:
- [ ] campo de data de upload preenchido em caso de sucesso.
- [ ] campo nulo em caso de falha simulada de upload.
- [ ] Confirmar resposta da API com download_url conforme matriz abaixo.

Matriz de validacao download_url:
- [ ] iTorrent download ON + data upload presente => URL iTorrent.
- [ ] iTorrent download ON + data upload ausente => comportamento atual (base_url ou None).
- [ ] iTorrent download OFF => comportamento atual (base_url ou None).

## 9. Definition of Done
- [ ] FR-1 a FR-5 implementados e validados.
- [ ] Sem regressao de tipagem e sem regressao de testes existentes.
- [ ] Logs minimos de sucesso/falha de upload iTorrent implementados.
- [ ] Documentacao de configuracao atualizada (README ou equivalente), se aplicavel.
