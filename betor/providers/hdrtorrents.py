from .provider import Provider

hdrtorrents = Provider(
    "hdrtorrents",
    "https://hdrtorrents.net",
    "{base_url}/pagina/{page}/",
    "{base_url}/index.php?busca={qs}",
    "{base_url}/pesquisa/{qs}/pagina/{page}/",
)
