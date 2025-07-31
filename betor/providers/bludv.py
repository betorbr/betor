from .provider import Provider

bludv = Provider(
    "bludv",
    "https://bludv.xyz",
    "{base_url}/page/{page}/",
    "{base_url}/?q={qs}",
)
