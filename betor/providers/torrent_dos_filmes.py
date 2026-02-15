from .provider import Provider

torrent_dos_filmes = Provider(
    "torrent-dos-filmes",
    "https://torrentdosfilmes-v2.xyz/?s",
    "https://torrentdosfilmes-v2.xyz/page/{page}/?s",
    "https://torrentdosfilmes-v2.xyz/?s={qs}",
    "https://torrentdosfilmes-v2.xyz/page/{page}/?s={qs}",
    append_domains=["torrentdosfilmes.se"],
)
