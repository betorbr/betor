from .provider import Provider

starck_filmes = Provider(
    "starck-filmes",
    "https://starckfilmes-v2.com",
    "https://www.starckfilmes-v2.com/page/{page}/",
    "https://www.starckfilmes-v2.com/?s={qs}",
    "https://www.starckfilmes-v2.com/page/{page}/?s={qs}",
    append_domains=["starckfilmes.com"],
)
