from .provider import Provider

bludv = Provider(
    "bludv",
    "https://bludvfilmes1.xyz",
    "{base_url}/page/{page}/",
    "{base_url}/?s={qs}",
    "{base_url}/page/{page}/?s={qs}",
    append_domains=[
        "bludv.net",
        "bludv-v1.xyz",
        "bludv1.xyz",
        "bludv1.com",
        "bludv2.xyz",
        "bludvfilmes.xyz",
    ],
    cf_clearance_domain=".bludvfilmes1.xyz",
)
