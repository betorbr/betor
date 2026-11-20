# BeTor

BeTor é o buscador de filmes e séries com o jeitinho mais brasileiro da internet.

## Provedores:

- [BLUDV](https://bludv1.com/)
- [Comando Torrents](https://comando.la/)
- [Torrent Dos Filmes](https://torrentdosfilmes.se/)
- [Starck Filmes](https://www.starckfilmes.site/)
- [Rede Torrent](https://redetorrent.com/)
- [Sem Torrent](https://semtorrent.com/)

### Solicitação de provedor

- Abra uma issue para avaliação dos manetedores.

## Documentação

### RestFul API

A API do Betor foi desenvolvida utilizando FastAPI, e a documentação dos endpoints pode ser acessada em `http://localhost:8000/docs`.

### Componentes

| Componente                    | Tipo / Tecnologia     | Função Principal                                                      | Comunicação / Observações                                                 |
|-------------------------------|-----------------------|-----------------------------------------------------------------------|---------------------------------------------------------------------------|
| **Betor API**                 | Python + FastAPI      | Orquestra raspagens, consulta items e acompanha status de tarefas     | MongoDB, Redis Cache, ScrapyD, Betor Items Queue (Celery API)             |
| **Betor ScrapyD**             | ScrapyD               | Executa e gerencia spiders remotamente                                | FlareSolverr (HTTP), MongoDB, Redis Cache, Redis Lock, Betor Items Queue  |
| **Betor Worker Items**        | Celery Worker         | Processa raw items em items enriquecidos                              | Consome Betor Items Queue, atualiza MongoDB, determina IMDb/TMDB          |
| **Betor Worker API Requests** | Celery Worker         | Consulta APIs externas                                                | Consome Betor API Requests Queue, faz requisições para API externas       |
| **Betor Worker Torrents**     | Celery Worker         | Consulta metadados de torrents e atualiza items                       | Consome Betor Torrent Queue, atualiza MongoDB                             |

## Executando com Docker

Para subir a stack completa do BeTor utilizando Docker, você pode utilizar um arquivo `docker-compose.yml`. As imagens oficiais do BeTor são publicadas no GitHub Container Registry (`ghcr.io/dougppaz/betor`).

### Serviços Externos (Infrastrutura)

#### Obrigatórios:
- **MongoDB**: Banco de dados principal para armazenamento de itens, metadados e provedores.
- **Redis**: Broker de mensagens para o Celery, cache e controle de locks.
- **FlareSolverr**: Utilizado pelos scrapers para contornar proteções Cloudflare dos sites dos provedores.

#### Opcionais:
- **InfluxDB e Grafana**: Para coleta e visualização de métricas de monitoramento.
- **Mongo Express**: Interface web para gerenciamento do MongoDB.
- **Nginx**: Servidor web estático para disponibilizar arquivos de torrents e dados estáticos baixados.

### Exemplo de `docker-compose.yml`

```yaml
version: '3.8'

services:
    mongodb:
        image: mongo:8
        ports:
            - "27017:27017"
        environment:
            MONGO_INITDB_ROOT_USERNAME: betor
            MONGO_INITDB_ROOT_PASSWORD: betor
        healthcheck:
            test: ["CMD", "mongosh", "localhost:27017/test", "--quiet", "--eval", "db.runCommand('ping').ok"]
            interval: 5s
            timeout: 10s
            retries: 5
            start_period: 10s

    redis:
        image: redis:8
        ports:
            - "6379:6379"
        healthcheck:
            test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
            interval: 5s
            timeout: 10s
            retries: 5
            start_period: 10s

    flaresolverr:
        image: ghcr.io/flaresolverr/flaresolverr:latest
        ports:
            - "8191:8191"

    celery-worker-items:
        image: ghcr.io/dougppaz/betor:latest
        command: ["celery", "-A", "betor.celery.app", "worker", "-Q", "items"]
        depends_on:
            redis:
                condition: service_healthy
        environment:
            - DATABASE_MONGO_DB_CONNECTION_URI=mongodb://betor:betor@mongodb:27017
            - DATABASE_REDIS_URL=redis://redis:6379/0
            - BETOR_CELERY_BACKEND_URL=redis://redis:6379/1
            - BETOR_CELERY_BROKER_URL=redis://redis:6379/1
            - SCRAPYD_BASE_URL=http://scrapyd:6800
            - FLARESOLVERR_BASE_URL=http://flaresolverr:8191

    celery-worker-api-requests:
        image: ghcr.io/dougppaz/betor:latest
        command: ["celery", "-A", "betor.celery.app", "worker", "-Q", "api-requests"]
        depends_on:
            redis:
                condition: service_healthy
        environment:
            - DATABASE_MONGO_DB_CONNECTION_URI=mongodb://betor:betor@mongodb:27017
            - DATABASE_REDIS_URL=redis://redis:6379/0
            - BETOR_CELERY_BACKEND_URL=redis://redis:6379/1
            - BETOR_CELERY_BROKER_URL=redis://redis:6379/1
            - SCRAPYD_BASE_URL=http://scrapyd:6800
            - FLARESOLVERR_BASE_URL=http://flaresolverr:8191

    celery-worker-torrents:
        image: ghcr.io/dougppaz/betor:latest
        command: ["celery", "-A", "betor.celery.app", "worker", "-Q", "torrents"]
        depends_on:
            redis:
                condition: service_healthy
        environment:
            - DATABASE_MONGO_DB_CONNECTION_URI=mongodb://betor:betor@mongodb:27017
            - DATABASE_REDIS_URL=redis://redis:6379/0
            - BETOR_CELERY_BACKEND_URL=redis://redis:6379/1
            - BETOR_CELERY_BROKER_URL=redis://redis:6379/1
            - SCRAPYD_BASE_URL=http://scrapyd:6800
            - FLARESOLVERR_BASE_URL=http://flaresolverr:8191
            - STORE_TORRENT_FILE_SAVE_URL=local:///torrents
            - STORE_TORRENT_FILE_PUBLIC_DOWNLOAD_BASE_URL=http://localhost:8001/torrents
        volumes:
            - torrents:/torrents
        ports:
            - "6881:6881"

    scrapyd:
        image: ghcr.io/dougppaz/betor:latest
        command: ["scrapyd"]
        depends_on:
            mongodb:
                condition: service_healthy
            redis:
                condition: service_healthy
            flaresolverr:
                condition: service_started
        environment:
            - DATABASE_MONGO_DB_CONNECTION_URI=mongodb://betor:betor@mongodb:27017
            - DATABASE_REDIS_URL=redis://redis:6379/0
            - BETOR_CELERY_BACKEND_URL=redis://redis:6379/1
            - BETOR_CELERY_BROKER_URL=redis://redis:6379/1
            - SCRAPYD_BASE_URL=http://scrapyd:6800
            - FLARESOLVERR_BASE_URL=http://flaresolverr:8191
        ports:
            - "6800:6800"

    betor-api:
        image: ghcr.io/dougppaz/betor:latest
        command: ["fastapi", "run", "betor/api/app.py"]
        depends_on:
            mongodb:
                condition: service_healthy
            redis:
                condition: service_healthy
            scrapyd:
                condition: service_started
        environment:
            - DATABASE_MONGO_DB_CONNECTION_URI=mongodb://betor:betor@mongodb:27017
            - DATABASE_REDIS_URL=redis://redis:6379/0
            - BETOR_CELERY_BACKEND_URL=redis://redis:6379/1
            - BETOR_CELERY_BROKER_URL=redis://redis:6379/1
            - SCRAPYD_BASE_URL=http://scrapyd:6800
            - FLARESOLVERR_BASE_URL=http://flaresolverr:8191
            - DOWNLOAD_ITEMS_STORE_SAVE_URL=local:///items-data
            - DOWNLOAD_ITEMS_STORE_PUBLIC_DOWNLOAD_BASE_URL=http://localhost:8001/items-data
        ports:
            - "8000:8000"
        volumes:
            - items-data:/items-data

    nginx:
        image: nginx:latest
        ports:
            - "8001:80"
        volumes:
            - torrents:/usr/share/nginx/html/torrents
            - items-data:/usr/share/nginx/html/items-data

volumes:
    torrents: {}
    items-data: {}
```
