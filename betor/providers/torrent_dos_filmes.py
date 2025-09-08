from .provider import Provider

torrent_dos_filmes = Provider(
    "torrent-dos-filmes",
    "https://torrentdosfilmes.se/?s",
    "https://torrentdosfilmes.se/page/{page}/?s",
    "https://torrentdosfilmes.se/?s={qs}",
    "https://torrentdosfilmes.se/page/{page}/?s={qs}",
)
