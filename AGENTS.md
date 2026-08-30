<!-- bmad:context -->
<!-- Verified 2026-08-30 against 1ff0bfc. Managed by bmad-project-context; edits inside this block are replaced on refresh. Keep anything you want preserved outside the markers. -->

## BeTor

P2P movie and TV series search engine. Python 3.13+, FastAPI for API, Scrapy for scraping, Celery for task processing, MongoDB + Redis for state. Tickets and demands tracked in GitHub issues and commits.

## Policy

- Never push code directly to main. Always branch and PR.
- Direct commits to main only for:
    - `poetry update` results (commit `poetry.lock`)
    - Release commits: `poetry version [major|minor|patch]` then commit `pyproject.toml` with message `release: x.x.x`
- Never edit generated files: `poetry.lock`, `coverage.xml`, `scrapyd-eggs/`, `.mypy_cache/`, `.pytest_cache/`

## Where things are

- API (FastAPI): `betor/` — endpoints, services, repositories
- Scrapers (Scrapy): `betor_scrapy/spiders/` — spider definitions
- Unit tests: `tests/` — test coverage, no external services needed
- Acceptance/integration tests: `acceptance_tests/` — full-stack validation with `docker compose -f acceptance-tests.docker-compose.yml`
- CI/CD: `.github/workflows/ci.yml` (linting, typing, unit tests), `release.yml` (Docker build on tags)

## Running and verifying

- Run unit tests: `poetry run pytest tests`
- Run acceptance tests: first `docker compose -f acceptance-tests.docker-compose.yml up -d`, then `poetry run pytest acceptance_tests`
- Linting, formatting, typing: `poetry run flake8`, `poetry run isort --profile black .`, `poetry run black .`, `poetry run mypy .`
- All commands must run through `poetry run` — do not invoke Python or tools directly

## Known pitfalls

- Never commit code changes directly to main — always create a feature branch and open a PR
- Acceptance tests require the full Docker Compose stack running; unit tests run in isolation
- Always use `poetry run` prefix, even for simple commands like pytest or linting tools

<!-- /bmad:context -->
