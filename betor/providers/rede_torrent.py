from .provider import Provider

rede_torrent = Provider(
    "rede-torrent",
    "https://redestorrents.com",
    "{base_url}/pagina/{page}/",
    "{base_url}/index.php?s={qs}",
    "{base_url}/pagina/{page}/?s={qs}",
)
