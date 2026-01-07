from .provider import Provider

sem_torrent = Provider(
    "sem-torrent",
    "https://semtorrent.com",
    "{base_url}/{page}/",
    "{base_url}/index.php?s={qs}",
    "{base_url}/{qs}/{page}/",
)
