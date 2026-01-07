# BeTor

BeTor é o buscador de filmes e séries com o jeitinho mais brasileiro da internet.

## Provedores:

- [BLUDV](https://bludv.xyz/)
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
