from .provider import Provider

starck_filmes = Provider(
    "starck-filmes",
    "https://www.starckfilmes-v8.com",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    append_domains=[
        "starckfilmes.com",
        "starckfilmes-v2.com",
        "starckfilmes-v7.com",
        "starckfilmes-v6.com",
    ],
)
