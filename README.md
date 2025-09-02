# BeTor

BeTor é o buscador P2P de filmes e séries com o jeitinho mais brasileiro da internet.

## Provedores:

- [BLUDV](https://bludv.xyz/)
- [Comando Torrents](https://comando.la/)

### Por vir

- [Torrent Dos Filmes](https://torrentdosfilmes.se/)
- [Starck Filmes](https://www.starckfilmes.site/)
- [Rede Torrent](https://redetorrent.com/)

## Documentação

### RestFul API

A API do Betor foi desenvolvida utilizando FastAPI, e a documentação dos endpoints pode ser acessada em `http://localhost:8000/docs`.

## Serviços e Arquitetura

![C4 Model: Container](https://www.plantuml.com/plantuml/png/ZLRDRjj64BxhAIP23muGMq2RKz0MiNwC6eXRrnBQOp0YH_B2-yFkZoovoCCKFUJKOv_0BzRP9RKXGx7mYTnTVjzy--tCBDyxZzO79KUlX2vaA0c-dxsTpDv-d1djKMYoFuv6hqhQy2lC5xzTptxvUGdttbVktMHYyV5YA_nzM0T7jc08QNzH63NneSBIVZUf9Eh8VovuzNp3NvoxoWfFRgAOVXAdtQIaNNhvTfHrv60JPVJMbEkBYcbEB5igXHjQtA3pM8bwUJIw9UkCFYkaO9rlO3pZc469qjWnZnPxKfKqx-2oag90BtO67caD9e0oQo7f3TnQyoZHsZT0lXY_7esM1-T9VLpi_Tc65yWPkQEuFhwAmsKQ9dQ6xW_mHo1eleAI76w4SL0Qc4aJoiG05Le43Duebl245h0Wv-9dmRAP10WMNOLRKXTHmjG4NQ8zdD7UazKeBolXEE3bxVKI5lMS6x-6FqS0BRb2bUjbs6x9UM4qOnXoVJDVmvT9O0gEq85vXgqiwLBeRGrQtSodS9ng89-oCrdTcho9lapZiv6JawnUhVdkEFXLa94f-NRmzoo5u0gTR-Rcmh5BsGVDsvN2UGJ18HqGMsPKXVeUWMTzOEy8F5hYVBXWWc_g7FnXtEG7A-w9MHOMgqDvL0prU1x3jr_9xiJpPvCEjYAhc1PeJqNmoBkDuagqGB0bTgWG_EugKP9r3I5OKiQZedYoEu5ns-bO0R9rZkCpqmSya8q7QnK-aKuO0nEOON5FZQF7ivglprBTpDSCk4blqt4Fowvm2MVNqhDjJrDwBAV3d4ekHKt7nOD6GmkQlZa9_62AXuoBWvV1VWqKAEFIw3JmKyUxoffOFfoQH_jkwvd6Walddl_HXJNQD1RsCk5tOn_8NaTpSZRKSv0cewypacGFpVIu5IKR3AIoqQIju8Gf6ilvl8VZheorhBGNkfa_7JqrDkaH57aiiJHr1JIGkiLa4JQhQDcU3AvrfDVkzjCe7yBuIaXibLYNN-HSIs46JdiWR6_tpSHmR0x9eNUnmxBXsfF5vy_FVnieZ3ewy3-9SqUorOno3ML7yoR6gzbjWdKHdTf8pzgDTN05WgUz3oY7uPtManjTfwFbfXTPVbgjXcYwvtRv1Kzf8p4dg6wFhHpABJ_pPJ5VtMzttLjiG4r6PoTp2qgLCUncHdxLRL2A9uGYELkokSz_RON6bt0qZIS-qfcqUd9mAK4TSJVubnnqB-zXvbDEB_H6i9NOP6GTgcb3QFEk8ssh-K3jVuxIxpmd72H07v8XFIC7I4xT-Zcrq_L_FSydEKpJ_ml89Ebtu2KaVUiIYL6vbYF7a2svCNQT6RPZ2DplDIyIqXFVkQIcM3omEq0mjOR3zPJqWhwOWBiKC-H_s5ppMVJHUJY7kyLojGcoAUhtJ1YK_0y0)

### Componentes

| Componente                  | Tipo / Tecnologia       | Função Principal                                                                 | Comunicação / Observações                                      |
|------------------------------|-----------------------|-------------------------------------------------------------------------------|----------------------------------------------------------------|
| **Betor API**                | Python + FastAPI      | Orquestra raspagens, consulta items e acompanha status de tarefas               | MongoDB, Redis Cache, ScrapyD, Betor Items Queue (Celery API) |
| **Betor ScrapyD**            | ScrapyD               | Executa e gerencia spiders remotamente                                          | FlareSolverr (HTTP), MongoDB, Redis Cache, Redis Lock, Betor Items Queue |
| **Betor Worker Items**       | Celery Worker         | Processa raw items em items enriquecidos, consulta APIs externas                | Consome Betor Items Queue, atualiza MongoDB, consulta IMDb/TMDB |
| **Betor Worker Torrents**    | Celery Worker         | Consulta metadados de torrents e atualiza items                                  | Consome Betor Torrent Queue, atualiza MongoDB                  |
