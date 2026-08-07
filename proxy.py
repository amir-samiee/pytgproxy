from pathlib import Path

import requests

from models import Proxy

proxy_resources = ["https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt"]


def fetch_proxies(urls=proxy_resources):
    news = set()
    for url in urls:
        response = requests.get(url)
        if response.ok:
            news.update(response.text.splitlines())
    return news


def refine_proxy_file(filepath, key=len):
    path = Path(filepath)
    proxies = set(path.read_text().splitlines())
    proxies = filter(lambda p: Proxy.from_uri(p), proxies)
    if key:
        proxies = sorted(proxies, key=key)
    path.write_text("\n".join(proxies))


if __name__ == "__main__":
    filename = "proxies.txt"
    with open(filename, "a") as file:
        file.write("\n")
        file.write("\n".join(fetch_proxies()))
    refine_proxy_file(filename)
