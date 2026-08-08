import csv
from collections.abc import Sequence
from pathlib import Path

import requests
from dotenv import dotenv_values

from models import Proxy

proxy_pools = (dotenv_values()["PROXY_POOLS"] or "").split()


def fetch_proxies(urls=proxy_pools):
    news = set()
    for i, url in enumerate(urls, 1):
        print(f"fetching resource {i}/{len(urls)}...", end="\r")
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


def load_proxies(path="proxies.txt"):
    path = Path(path)
    uris = path.read_text().splitlines()
    return [proxy for uri in uris if (proxy := Proxy.from_uri(uri))]


def dump_results(results: Sequence, path="results.csv", valid_only=True):
    if valid_only:
        results = [res for res in results if res[0] > 0]
    with open(path, "w") as file:
        writer = csv.writer(file)
        writer.writerows(results)


if __name__ == "__main__":
    filename = "proxies.txt"
    with open(filename, "a") as file:
        file.write("\n")
        file.write("\n".join(fetch_proxies()))
    refine_proxy_file(filename)
