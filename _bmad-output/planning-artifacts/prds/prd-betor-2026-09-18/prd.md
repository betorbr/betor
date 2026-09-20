---
title: Integracao iTorrent para cache de arquivos .torrent
status: draft
created: 2026-09-18
updated: 2026-09-18
---

# PRD: Integracao iTorrent para cache de arquivos .torrent

## 0. Document Purpose
Este PRD define como o BeTor deve integrar o servico iTorrent para cache publico de arquivos .torrent, com controles explicitos de upload e download por configuracao. O objetivo e alinhar produto, API e implementacao para reduzir perda de disponibilidade de torrents apos longos periodos sem download, mantendo compatibilidade com o fluxo atual de obtencao de metadata via libtorrent e serializacao em `ItemSchema`.

## 1. Vision
Hoje o BeTor ja gera/salva arquivo .torrent no fluxo de `UpdateItemTorrentInfoService`, mas a disponibilidade final do download depende do armazenamento atual configurado por `store_torrent_file.save_url/public_download_base_url`. A integracao com iTorrent adiciona um provedor de cache especializado para esse arquivo, permitindo URL publica padronizada por info hash e maior resiliencia para consumo posterior.

A experiencia desejada e: quando habilitado, o sistema faz upload do .torrent para o iTorrent no momento da coleta de metadata, registra quando isso aconteceu e usa o iTorrent como origem de download ao expor `download_url`. Isso permite ao cliente entender validade temporal desse cache (especialmente considerando a janela de 12 meses sem downloads).

## 2. Target User

### 2.1 Jobs To Be Done
- Como mantenedor da plataforma, quero controlar por configuracao se o BeTor envia .torrent para iTorrent, para ativar/desativar integracao sem alterar codigo.
- Como consumidor da API de itens, quero receber um `download_url` funcional para obter o .torrent quando a funcionalidade estiver habilitada.
- Como operador, quero saber quando o .torrent foi enviado ao iTorrent para avaliar risco de expiracao do cache.

### 2.2 Key User Journeys
- **UJ-1. Operador habilita upload para iTorrent e novos torrents passam a ser publicados**
  - **Persona + contexto:** DevOps ajusta variaveis de ambiente de integracao de torrents.
  - **Entry state:** Servico em execucao com nova configuracao aplicada.
  - **Path:** pipeline processa item -> `get_info_from_lt_session` obtem metadata -> upload para iTorrent e executado.
  - **Climax:** `TorrentInfo` retorna com metadados e timestamp de upload preenchido.
  - **Resolution:** item persiste info com trilha temporal do envio.

- **UJ-2. Cliente da API usa URL do iTorrent para baixar o .torrent**
  - **Persona + contexto:** integrador consome endpoint de itens para iniciar download.
  - **Entry state:** item possui `download_path` e download por iTorrent habilitado.
  - **Path:** cliente chama endpoint -> `ItemSchema.download_url` e calculado -> cliente baixa do iTorrent.
  - **Climax:** URL no formato oficial do iTorrent resolve para o arquivo.
  - **Resolution:** cliente conclui download sem depender de URL custom de storage.

## 3. Glossary
- **iTorrent** — servico externo de cache de arquivos .torrent com API de automacao.
- **Upload para iTorrent** — envio do arquivo .torrent gerado para o endpoint de automacao do iTorrent.
- **Download via iTorrent** — exposicao de URL publica do iTorrent como fonte de download do .torrent.
- **Timestamp de upload iTorrent** — data/hora em que o upload do .torrent foi concluido no iTorrent.
- **Info hash** — identificador do torrent utilizado na URL publica do iTorrent, com caracteres hexadecimais A-F em maiusculo.

## 4. Features

### 4.1 Flags de configuracao para integracao iTorrent
**Description:** Uma classe dedicada `ITorrentSettings` deve expor as flags de integracao iTorrent, separando responsabilidades de armazenamento generico de `.torrent` (`StoreTorrentFileSettings`) e da automacao do iTorrent.

**Functional Requirements:**

#### FR-1: Flag de upload iTorrent
Sistema deve disponibilizar parametro de configuracao em `ITorrentSettings` para ativar/desativar upload para iTorrent com padrao `true`. Realiza UJ-1.

**Consequences (testable):**
- Com variavel ausente, upload iTorrent e tratado como habilitado.
- Com valor `false`, o fluxo nao tenta upload no iTorrent.

#### FR-2: Flag de download iTorrent
Sistema deve disponibilizar parametro de configuracao em `ITorrentSettings` para ativar/desativar uso de URL de download do iTorrent com padrao `true`. Realiza UJ-2.

**Consequences (testable):**
- Com variavel ausente, `download_url` pode apontar para iTorrent quando houver dados necessarios.
- Com valor `false`, `download_url` nao usa URL do iTorrent.

### 4.2 Metadado temporal de upload no contrato de dominio
**Description:** `TorrentInfo` deve registrar quando o upload para iTorrent ocorreu para suportar avaliacao de validade do cache ao longo do tempo.

**Functional Requirements:**

#### FR-3: Campo de data de upload no TorrentInfo
`TorrentInfo` deve incluir campo opcional para timestamp do upload no iTorrent. Realiza UJ-1.

**Consequences (testable):**
- Quando upload iTorrent e executado com sucesso, campo e preenchido com data/hora do evento.
- Quando upload nao e executado (flag desligada ou sem tentativa), campo permanece `None`.
- O tipo e formato de persistencia devem seguir o padrao atual da aplicacao: `datetime` nativo (mesmo padrao usado em `occurred_at`, `inserted_at` e `updated_at`).

### 4.3 Geracao de download_url usando iTorrent
**Description:** `ItemSchema.download_url` deve priorizar URL publica do iTorrent quando download por iTorrent estiver habilitado, usando funcao util compartilhada para extracao de info hash a partir de magnet URI.

**Functional Requirements:**

#### FR-4: URL padrao iTorrent no schema
`download_url` deve ser calculada como `http://itorrents.net/torrent/<INFO_HASH>.torrent` quando o download via iTorrent estiver habilitado e houver base para gerar o hash. Realiza UJ-2.

**Consequences (testable):**
- URL gerada usa info hash em uppercase para A-F, conforme regra do iTorrent.
- Sem dados suficientes para hash/identificador, `download_url` segue nulo.
- Com download via iTorrent habilitado e sem data de upload registrada no item, `download_url` deve manter o comportamento atual (usar `public_download_base_url` quando configurado; senao, `None`).
- A extracao do hash deve reutilizar util compartilhada baseada em `torf.Magnet.from_string`, evitando duplicacao de parsing.

**Out of Scope:**
- Nao criar encurtador, proxy interno ou assinatura de URL.

### 4.4 Upload para iTorrent no fluxo de metadata
**Description:** `get_info_from_lt_session` deve executar upload para iTorrent quando a flag de upload estiver ativa, preservando o fluxo de retorno de `TorrentInfo`.

**Functional Requirements:**

#### FR-5: Upload condicional para iTorrent
Ao concluir obtencao do `.torrent`, o servico deve enviar o arquivo para automacao iTorrent quando upload estiver habilitado. Realiza UJ-1.

**Consequences (testable):**
- O upload e acionado apenas quando `upload_to_itorrent` estiver `true`.
- Em sucesso, o retorno inclui timestamp de upload e caminho/identificador consistente para gerar download.
- Em falha no upload iTorrent, o processamento continua e o campo de data de upload nao e preenchido (ou permanece nulo quando sem valor anterior).

**Feature-specific NFRs:**
- Observabilidade: logs devem permitir distinguir sucesso/falha de upload iTorrent.
- Confiabilidade: nao introduzir regressao no timeout de metadata da sessao libtorrent.

## 5. Non-Goals (Explicit)
- Nao implementar politica automatica de reupload por expiracao de 12 meses nesta entrega.
- Nao alterar estrategia de scraping/provedores de magnet links.
- Nao redesenhar contratos de endpoint alem de `download_url` e novo campo de metadado de upload em estruturas relacionadas.

## 6. MVP Scope

### 6.1 In Scope
- Nova classe `ITorrentSettings` com parametros dedicados para upload/download e endpoints/base URL do iTorrent.
- Upload condicional no fluxo de `get_info_from_lt_session`.
- Campo temporal no `TorrentInfo` para data de upload ao iTorrent.
- Ajuste de `download_url` para gerar URL oficial iTorrent quando habilitado.
- Funcao util compartilhada para extrair info hash de magnet URI e reutilizacao no schema e no servico de trackers.

### 6.2 Out of Scope for MVP
- Rotina de limpeza/revalidacao periodica de torrents antigos.
- Dashboard de idade de cache.
- Fallback multi-provedor para download de .torrent.

## 7. Success Metrics

**Primary**
- **SM-1**: >= 95% dos torrents processados com upload habilitado possuem registro de timestamp de upload no iTorrent. Valida FR-3, FR-5.
- **SM-2**: >= 99% das respostas com download habilitado e dados disponiveis expoem `download_url` no formato oficial iTorrent. Valida FR-4.

**Secondary**
- **SM-3**: zero regressao nos fluxos existentes de update de metadata em testes automatizados de unidade/contrato. Valida FR-1, FR-2, FR-5.

**Counter-metrics (do not optimize)**
- **SM-C1**: aumento de timeout medio do processamento de metadata > 20% nao e aceitavel. Counterbalances SM-1.

## 8. Open Questions
- Nenhuma questao aberta para esta iteracao.

## 9. Assumptions Index
- Nenhuma assuncao pendente para esta iteracao.
