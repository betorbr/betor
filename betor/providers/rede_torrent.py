from .provider import Provider

rede_torrent = Provider(
    "rede-torrent",
    "https://redestorrents.com",
    "https://redestorrents.com/pagina/{page}/",
    "https://redestorrents.com/index.php?s={qs}",
    "https://redestorrents.com/pagina/{page}/?s={qs}",
)
