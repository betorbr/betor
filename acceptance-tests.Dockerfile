FROM python:3.13-alpine AS build-requirements

RUN pip install poetry==2.1.4 \
        && poetry self add poetry-plugin-export

WORKDIR /betor

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry export -f requirements.txt --with dev --output requirements.txt

FROM python:3.13-alpine

WORKDIR /betor

COPY --from=build-requirements /betor/requirements.txt .
RUN pip install -r requirements.txt

COPY betor betor
COPY betor_scrapy betor_scrapy
COPY acceptance_tests acceptance_tests
