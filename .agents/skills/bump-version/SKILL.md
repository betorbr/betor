---
name: bump-version
description: Avalia o histórico de commits para determinar o nível de bump (patch, minor, major), atualiza a versão no pyproject.toml e na app do FastAPI, e cria o commit de release e git tag correspondentes (com suporte a release candidates). Use quando precisar lançar uma nova versão ou release candidate no projeto.
---

# Skill de Bump Version (BeTor)

Esta skill é responsável por automatizar o processo de lançamento de novas versões e release candidates no projeto **BeTor**, seguindo estritamente as convenções do repositório.

## O que a skill faz:

1. **Análise do Histórico de Commits**:
   - Identifica o commit do último lançamento (`release: x.x.x` ou `release: x.x.x-rcY`).
   - Coleta todas as mensagens de commit desde a última release até o `HEAD`.
   - Avalia automaticamente o nível do bump (`major`, `minor` ou `patch`):
     - **major**: Se houver alguma mensagem de commit contendo `BREAKING CHANGE` ou `major:`.
     - **minor**: Se houver commits do tipo `feat:` (novas funcionalidades).
     - **patch**: Se houver apenas correções (`fix:`), refatorações (`refactor:`), testes (`test:`), docs, dependências, etc., sem `feat:` ou `major`.

2. **Gerenciamento de Versão e Release Candidates (RC)**:
   - **Release Estável Padrão**: Incrementa o nível determinado (ex: `1.58.0` -> `1.59.0` para minor).
   - **Modo Release Candidate (`--rc`)**: Se a versão anterior for estável, gera a primeira RC (ex: `1.59.0-rc0`). Se a versão atual já for uma RC (ex: `1.58.0-rc0`), incrementa o dígito da RC (`1.58.0-rc1`).
   - **Promoção de RC (`--promote`)**: Se a versão atual for um release candidate (`1.58.0-rc0`), remove o sufixo `-rcY` para transformá-la na release estável final (`1.58.0`).
   - **Versão no FastAPI**: A versão da app FastAPI (`betor/api/app.py`) é sempre atualizada com a versão base correspondente (sem sufixo `-rcY`), conforme exigido pelo projeto.

3. **Atualização de Arquivos, Commit e Tag**:
   - Atualiza `pyproject.toml` e `betor/api/app.py`.
   - Cria o commit git com a mensagem no padrão `"release: x.x.x"` ou `"release: x.x.x-rcY"`.
   - Adiciona a tag git no padrão `vx.x.x` ou `vx.x.x-rcY`.

---

## Como executar

Execute o script auxiliar localizado em `scripts/bump.py` usando `poetry run python`:

- **Bump normal (automático baseado nos commits)**:
  ```bash
  poetry run python .agents/skills/bump-version/scripts/bump.py
  ```

- **Criar / Incrementar um Release Candidate**:
  ```bash
  poetry run python .agents/skills/bump-version/scripts/bump.py --rc
  ```

- **Promover Release Candidate para Release Estável**:
  ```bash
  poetry run python .agents/skills/bump-version/scripts/bump.py --promote
  ```

- **Forçar um nível específico de bump (ex: patch)**:
  ```bash
  poetry run python .agents/skills/bump-version/scripts/bump.py --level patch
  ```

- **Simular alterações sem modificar arquivos ou git (Dry-run)**:
  ```bash
  poetry run python .agents/skills/bump-version/scripts/bump.py --dry-run
  ```
