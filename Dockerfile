FROM python:3.13-alpine AS build-requirements

RUN pip install poetry==2.1.3 \
        && poetry self add poetry-plugin-export

WORKDIR /betor

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry export -f requirements.txt --output requirements.txt

FROM python:3.13-alpine

WORKDIR /betor

COPY --from=build-requirements /betor/requirements.txt .
RUN pip install -r requirements.txt && pip install flower scrapyd-client

COPY betor betor
COPY betor_scrapy betor_scrapy
COPY scrapy.cfg .
COPY scrapyd.conf .

RUN mkdir -p ./scrapyd-eggs/betor && scrapyd-deploy --build-egg=./scrapyd-eggs/betor/betor.egg
