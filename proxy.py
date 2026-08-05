from pathlib import Path

from models import Proxy


def refine_proxy_file(filepath, key=len):
    path = Path(filepath)
    proxies = set(path.read_text().splitlines())
    proxies = filter(lambda p: Proxy.from_uri(p).port in [80, 443, 8443], proxies)
    if key:
        proxies = sorted(proxies, key=key)
    path.write_text("\n".join(proxies))


if __name__ == "__main__":
    refine_proxy_file("proxies.txt")
