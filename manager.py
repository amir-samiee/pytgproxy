import csv
import logging
from collections.abc import Sequence
from dataclasses import fields, is_dataclass
from pathlib import Path

import requests
from dotenv import dotenv_values
from rich.logging import RichHandler


def resolve_name(obj):
    o_type = obj if isinstance(obj, str) else type(obj).__name__
    o_type = o_type[0].lower() + o_type[1:]
    return o_type


def asdict(obj):
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            result[resolve_name(f.name)] = asdict(getattr(obj, f.name))
        result["@type"] = resolve_name(obj)
        return result
    return obj


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


def dump_results(results: Sequence, path="results.csv", valid_only=True, mode="w"):
    if valid_only:
        results = [res for res in results if res[0] > 0]
    with open(path, mode) as file:
        if mode == "a":
            file.write("\n")
        writer = csv.writer(file)
        writer.writerows(results)


def setup_logging(level=logging.INFO):
    handlers = [
        RichHandler(log_time_format="%X", show_path=False),
        logging.FileHandler(".log", "a"),
    ]
    logging.basicConfig(level=level, handlers=handlers)


if __name__ == "__main__":
    filename = "proxies.txt"
    with open(filename, "a") as file:
        file.write("\n")
        file.write("\n".join(fetch_proxies()))
    refine_proxy_file(filename)
