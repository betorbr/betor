---
id: SPEC-itorrent-upload-verification
companions: []
---

# Verificação de Upload e Disponibilidade do iTorrent

## Why

O fluxo de upload do torrent para o iTorrent precisa ser verificado por uma condição objetiva de disponibilidade pública. O sistema já registra o momento do upload, mas esse registro só é confiável se a resposta do provedor indicar sucesso e se o arquivo estiver realmente acessível no endpoint público do serviço.

## Capabilities

- **CAP-1**
  - **intent:** O sistema deve aceitar como upload bem-sucedido apenas respostas do provedor que contenham um hash ou link válido para o torrent.
  - **success:** `extract_itorrent_info_hash()` reconhece links do tipo `/torrent/<hash>.torrent` e retorna o hash hexadecimal de 40 caracteres.

- **CAP-2**
  - **intent:** O sistema deve confirmar que o arquivo realmente existe no endpoint público do iTorrent após o upload.
  - **success:** Após o POST bem-sucedido, o fluxo executa um `HEAD` para o link público do torrent e considera o upload válido somente quando a resposta HTTP indica que o arquivo está disponível.

- **CAP-3**
  - **intent:** O endpoint público de download deve ser construído a partir da base correta `https://itorrents.net/torrent/` sem duplicar barras e com HTTPS.
  - **success:** o campo `download_url` usa a URL pública canônica do iTorrent e o hash no caminho do torrent.

## Constraints

- Manter compatibilidade com o contrato atual de `itorrent_uploaded_at`.
- Não aceitar uploads sem evidência de disponibilidade pública do arquivo.
- Preservar fallback para `download_path` local quando o upload do iTorrent não estiver disponível.
- Usar `HEAD` apenas como verificação final de existência do arquivo, sem substituir a validação de hash na resposta do upload.

## Non-goals

- Alterar a lógica de persistência do MongoDB ou do schema público além do campo de URL e do timestamp de upload.
- Resolver comportamento inconsistente do provedor fora do fluxo de validação do arquivo publicado.

## Success signal

Uma execução real do fluxo com um `.torrent` válido deve produzir:

1. POST para `https://itorrents.net/upload.php` com resposta positiva;
2. extração correta do hash de sucesso;
3. `HEAD https://itorrents.net/torrent/<hash>.torrent` retornando status de existência; em caso de 520 ou 404 para uma variante, a verificação deve testar a variante em lowercase e uppercase;
4. campo `itorrent_uploaded_at` preenchido somente quando todas as verificações forem satisfeitas.
