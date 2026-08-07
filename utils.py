from pathlib import Path

from models import Proxy


def load_proxies(path="proxies.txt", keepuri=False):
    path = Path(path)
    uris = path.read_text().splitlines()
    return [
        uri if keepuri else proxy  ##
        for uri in uris
        if (proxy := Proxy.from_uri(uri))
    ]
