from .provider import Provider

rede_torrent = Provider(
    "rede-torrent",
    "https://redetorrent.com",
    "https://redetorrent.com/{page}/",
    "https://redetorrent.com/index.php?s={qs}",
    "https://redetorrent.com/{page}/?s={qs}",
)
