# AI Agent Instructions for BeTor

## Purpose
This repository implements a Python-based media search backend that combines FastAPI, Scrapy, Celery, MongoDB, Redis, and Scrapyd.

## Key project facts
- Python 3.13 with dependency management via Poetry.
- Package roots: `betor` and `betor_scrapy`.
- CI uses `poetry install`, `poetry run flake8`, `poetry run isort --profile black .`, `poetry run black .`, `poetry run mypy .`, and `poetry run pytest .`.
- Code is organized around API, providers, services, repositories, external API integrations, and Scrapy spiders/pipelines.

## Primary entry points
- `betor/api/app.py` — FastAPI application.
- `betor/celery/app.py` — Celery application and task registration.
- `betor_scrapy/settings.py` — Scrapy settings and pipeline configuration.
- `docker-compose.yml` — local orchestrated environment for API, Scrapyd, Celery workers, Redis, MongoDB, and related services.

## Important directories
- `betor/api/` — API endpoints and app wiring.
- `betor/celery/` — background task definitions.
- `betor/providers/` — provider-specific scraper logic.
- `betor/services/` — business workflows and item enrichment.
- `betor/repositories/` — data persistence logic.
- `betor/external_apis/` — TMDB/IMDB integrations.
- `betor_scrapy/spiders/` — Scrapy spiders for each torrent provider.
- `betor_scrapy/pipelines/` — Scrapy item processing, raw item normalization, and persistence.

## Style and conventions
- Use the existing format rules from `black` and `isort`.
- The code uses async/await widely; preserve async behavior in services and pipelines.
- Tests are under `tests/`; run `poetry run pytest .`.
- `pytest.ini` enables coverage for `betor` and `betor_scrapy`.

## What agents should do
- Prefer editing within `betor/` and `betor_scrapy/` for feature, bugfix, or refactor work.
- When adding or changing spiders, keep provider-specific parsing isolated in `betor_scrapy/spiders/`.
- When adjusting business rules, update `betor/services/` and corresponding tests.
- For data model changes, verify `betor/entities/`, repository logic, and API contracts.

## Useful references
- `README.md` — architecture overview and component relationships.
- `pyproject.toml` — package metadata, dependencies, and developer tooling.
- `.github/workflows/ci.yml` — authoritative CI commands.
- `docker-compose.yml` — local environment with API, Scrapyd, Celery, Redis, MongoDB.

## Additional guidance
- Do not assume there is a frontend component in this repository.
- Keep changes focused and test-driven whenever possible.
- If behavior depends on external providers, prefer adding unit tests that isolate parsing and transformation logic.
