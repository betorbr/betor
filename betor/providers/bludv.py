from .provider import Provider

bludv = Provider(
    "bludv",
    "https://bludvfilmes.xyz",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    append_domains=[
        "bludv.net",
        "bludv-v1.xyz",
        "bludv1.xyz",
        "bludv1.com",
        "bludv2.xyz",
    ],
    cf_clearance_domain=".bludvfilmes.xyz",
)
