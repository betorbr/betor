from .provider import Provider

starck_filmes = Provider(
    "starck-filmes",
    "https://www.starckfilmes-v6.com",
    "https://www.starckfilmes-v6.com/page/{page}/",
    "https://www.starckfilmes-v6.com/?s={qs}",
    "https://www.starckfilmes-v6.com/page/{page}/?s={qs}",
    append_domains=["starckfilmes.com", "starckfilmes-v2.com", "starckfilmes-v7.com"],
)
